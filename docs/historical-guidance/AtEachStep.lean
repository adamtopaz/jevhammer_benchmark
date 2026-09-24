module

public meta import JevPilot.Search
public meta import JevFinish
public meta import JevFinish.Advanced
public meta import JevFinish.Planned
public meta import JevFinish.Certificate
public meta import Bench.Competitor
public meta import Bench.OptionalFinisher
public meta import Mathlib.Tactic.TacticAnalysis.Declarations

public meta section

/-! An opt-in pass for mathlib's existing TacticAnalysis/tryAtEachStep framework.
Unlike the stock reporter, record failures, denominators, costs, and every depth.
The Python driver recompiles copies of original source files, never imported targets. -/
namespace Bench.AtEachStep
open Lean Meta Elab Command JevPilot

structure Settings where
  phase : String
  moduleName : String
  outputDir : String
  sites : Array String := #[]
  injectedBytes : Nat := 36
  injectedLines : Nat := 1
  premiseApiBaseUrl : String := "http://127.0.0.1:18080"
  depths : Array Nat := #[8, 16, 32]
  modes : Array String := #["stock", "structural"]
  maxNodes : Nat := 256
  maxTrials : Nat := 160
  maxCandidates : Nat := 24
  maxCalls : Nat := 2
  maxMillis : Nat := 10000
  maxHeartbeats : Nat := 200000
  maxRequests : Nat := 384
  maxInputTokens : Nat := 2000000
  maxRequestBytes : Nat := 80000
  model : String := "jev-1.13.0"
  live : Bool := false
  chargeCachedLatency : Bool := false
  warmHammerImports : Bool := false
  rotateModes : Bool := false
  deriving FromJson, ToJson

structure Budget where
  attempts : Nat := 0
  inputTokens : Nat := 0
  outputTokens : Nat := 0
  deriving FromJson, ToJson

structure ExternalStats where
  freshCalls : Nat := 0
  cacheHits : Nat := 0
  blocked : Bool := false
  errors : Array String := #[]
  chargedCacheMs : Nat := 0
  unreportedUsageCalls : Nat := 0
  deriving ToJson

/-- Reservations are handled before transport; charge reported usage even when
answer validation rejects the response. Missing usage is tracked separately. -/
def chargeOutcome (budget : Budget) (outcome : TypeSafe.Outcome) : Budget :=
  let usage := outcome.reportedUsage.getD {}
  { budget with
    inputTokens := budget.inputTokens + usage.inputTokens.getD 0
    outputTokens := budget.outputTokens + usage.outputTokens.getD 0 }

initialize settingsRef : IO.Ref (Option Settings) ← IO.mkRef none
initialize seen : IO.Ref (Std.HashSet String) ← IO.mkRef {}
initialize clientRef : IO.Ref (Option TypeSafe.Client) ← IO.mkRef none
/-- Updated by our final linter after each source command. The standard InfoTree
context can contain the *completed* declaration, which is unsafe for library search. -/
initialize previousEnvironment : IO.Ref (Option Environment) ← IO.mkRef none
initialize warmed : IO.Ref Bool ← IO.mkRef false

private def settings : IO (Option Settings) := do
  if let some s ← settingsRef.get then return some s
  let some path ← IO.getEnv "JEVPILOT_EACH_STEP_CONFIG" | return none
  let s ← IO.ofExcept (Json.parse (← IO.FS.readFile path) >>= fromJson?)
  settingsRef.set (some s)
  return some s

private def appendJson (s : Settings) (file : String) (j : Json) : IO Unit := do
  let h ← IO.FS.Handle.mk (System.FilePath.mk s.outputDir / file) .append
  h.putStrLn j.compress
  h.flush

private def readJson (path : System.FilePath) : IO Json :=
  IO.FS.readFile path >>= fun text => IO.ofExcept (Json.parse text)

/-- The driver holds an exclusive lock and runs processes sequentially. Atomic replacement
also leaves a readable reservation ledger if a Lean process is killed mid-request. -/
private def atomicJson (path : System.FilePath) (j : Json) : IO Unit := do
  let tmp := System.FilePath.mk (path.toString ++ ".tmp")
  IO.FS.writeFile tmp j.compress
  IO.FS.rename tmp path

/-- Keep initial locals once; previews explicitly inherit them. Preserve full context
when it isn't an extension of the initial context (never guess that locals agree). -/
def compactBranches (state : Json) (branches : Array Json) : Array Json := Id.run do
  let base := (state.getObjValD "context").getArr?.toOption.getD #[]
  return branches.map fun b =>
    let goals := (b.getObjValD "remaining").getArr?.toOption.getD #[]
    let goals := goals.map fun g =>
      let ctx := (g.getObjValD "context").getArr?.toOption.getD #[]
      if ctx.size >= base.size && ctx.extract 0 base.size == base then
        Json.mkObj [("goal", g.getObjValD "goal"),
          ("additional_context", .arr (ctx.extract base.size ctx.size))]
      else g
    Json.mkObj [("action", b.getObjValD "action"), ("remaining", .arr goals)]

private def rankingFromJson (j : Json) : IO Search.Ranking := do
  return {
    order := ← IO.ofExcept (fromJson? (j.getObjValD "order"))
    -- Cache hits did not incur this response's original token usage again.
    model := ← IO.ofExcept (fromJson? (j.getObjValD "model")) }

private def getClient : IO TypeSafe.Client := do
  if let some c ← clientRef.get then return c
  let c ← (TypeSafe.Client.fromPass (config := {
    maxRetries := 0, timeoutSeconds := 5, connectTimeoutSeconds := 5 })).toIO
    (IO.userError ∘ toString)
  clientRef.set (some c)
  return c

/-- Shared on-disk cache freezes decisions across depths. Cache lookup includes the
entire request, pinned model, and prompt version; hash collisions are checked, not trusted. -/
def cachedRanker (s : Settings) (site : String) (extra : IO.Ref ExternalStats)
    (finish : Bool := false) : Search.Ranker :=
    fun state branches => do
  let req : TypeSafe.Request ← if finish && Decision.uses state then
    IO.ofExcept (Decision.request state branches s.model)
    else pure <| if finish then Advanced.rankingRequest state branches s.model else {
    model := s.model
    state := state
    questions := #[("branch", .choice (.str
      "Guide backward proof search in Lean 4. Each option is an application Lean has checked. Rank options by the prospects of proving ALL remaining goals. Every remaining goal inherits the state's context plus its additional_context, unless an explicit full context is supplied. Prefer concrete progress over circular restatements, unnecessary generalization, and arbitrary witness choices. Which branch should be explored first?")
      ((compactBranches state branches).mapIdx fun i b => (toString i, b)))] }
  let key := (if finish then "finish-v1:" else "compact-v1:") ++ (toJson req).compress
  let dir := System.FilePath.mk s.outputDir
  let path := dir / "cache" / s!"{hash key}.json"
  if ← path.pathExists then
    let j ← readJson path
    unless j.getObjValD "key" == .str key do throw (IO.userError "ranking cache hash collision")
    extra.modify fun e => { e with cacheHits := e.cacheHits + 1 }
    if s.chargeCachedLatency then
      let some elapsed := (j.getObjValD "elapsedMs").getNat?.toOption
        | extra.modify (fun e => { e with blocked := true })
          throw (IO.userError "cached decision lacks recorded latency")
      IO.sleep (UInt32.ofNat elapsed)
      extra.modify fun e => { e with chargedCacheMs := e.chargedCacheMs + elapsed }
    if let .str message := j.getObjValD "error" then
      extra.modify fun e => { e with errors := e.errors.push message }
      throw (IO.userError message)
    return ← rankingFromJson j
  let budgetPath := dir / "budget.json"
  let b : Budget ← IO.ofExcept (fromJson? (← readJson budgetPath))
  if !s.live || b.attempts >= s.maxRequests || b.inputTokens >= s.maxInputTokens ||
      key.utf8ByteSize > s.maxRequestBytes then
    extra.modify fun e => { e with blocked := true }
    throw (IO.userError "uncached ranking blocked by live/request/token/payload budget")
  -- Reserve before any IO that might send a request; no retries at the client layer.
  atomicJson budgetPath (toJson { b with attempts := b.attempts + 1 })
  extra.modify fun e => { e with freshCalls := e.freshCalls + 1 }
  let requestStart ← IO.monoMsNow
  let outcomeMetadata ← IO.mkRef Json.null
  try
    let outcome ← (← getClient).systemOneOutcome req
    outcomeMetadata.set <| Json.mkObj [
      ("reportedUsage", toJson outcome.reportedUsage),
      ("choiceDiagnostics", toJson outcome.choiceDiagnostics)]
    let usage := outcome.reportedUsage.getD {}
    if usage.inputTokens.isNone || usage.outputTokens.isNone then
      extra.modify fun e => { e with unreportedUsageCalls := e.unreportedUsageCalls + 1 }
    -- Charge a received response even if its ranking later fails validation.
    let updated := chargeOutcome { b with attempts := b.attempts + 1 } outcome
    atomicJson budgetPath (toJson updated)
    let response ← IO.ofExcept (outcome.result.mapError toString)
    let order ← if finish && Decision.uses state then do
        pure (← Decision.ranking state branches response).order
      else if finish then do
        let ranking ← Finish.responseRanking response branches.size
          (state.getObjValD "independent_scores" == .bool true)
        pure ranking.order
      else do
        let answer ← IO.ofExcept (response.choice? "branch")
        let prob := fun i => (answer.probabilities.find? (fun (k, _) => k == toString i)).map Prod.snd |>.getD 0
        pure <| (List.range branches.size).toArray.qsort fun i j =>
          if prob i == prob j then i < j else prob i > prob j
    let j := Json.mkObj [("key", toJson key), ("site", toJson site),
      ("model", toJson response.model), ("order", toJson order),
      ("elapsedMs", toJson ((← IO.monoMsNow) - requestStart)),
      ("outcome", ← outcomeMetadata.get),
      ("request", toJson req), ("response", toJson response)]
    atomicJson path j
    return { order, model := response.model, usage := response.usage }
  catch e =>
    let message := toString e
    extra.modify fun x => { x with errors := x.errors.push message }
    -- Also freeze failures, so later depths don't get a hidden second chance.
    atomicJson path (Json.mkObj [("key", toJson key), ("site", toJson site), ("error", toJson message),
      ("elapsedMs", toJson ((← IO.monoMsNow) - requestStart)),
      ("outcome", ← outcomeMetadata.get)])
    throw e

private def runTrial (s : Settings) (i : Mathlib.TacticAnalysis.TacticNode)
    (goal : MVarId) (site : String) (mode : String) (depth : Nat) : CommandElabM Unit := do
  let stats ← IO.mkRef ({} : Search.Stats)
  let finishStats ← IO.mkRef ({} : Finish.Stats)
  let advancedStats ← IO.mkRef ({} : Advanced.Stats)
  let plannedStats ← IO.mkRef ({} : Planned.Stats)
  let optionalStats ← IO.mkRef Json.null
  let isPlannedOptional := mode.startsWith "planned_"
  let isOptional := mode.startsWith "hammer_" || mode.startsWith "neural_" || isPlannedOptional
  let isPlanned := mode.startsWith "v3_"
  let isAdvanced := mode.startsWith "v2_"
  let isFinish := !["stock", "structural", "jev"].contains mode
  let extra ← IO.mkRef ({} : ExternalStats)
  let start ← IO.monoMsNow
  let mut solved := false
  let mut message := ""
  let mut proof := ""
  let mut used : Array String := #[]
  let mut certificate := Json.null
  try
    -- Use the original tactic's BEFORE context, not the final InfoTree assignments.
    let ctx := { i.ctxI with mctx := i.tacI.mctxBefore }
    let result ← ctx.runTactic i.tacI goal fun g => g.withContext do
      Search.withHeartbeatBudget s.maxHeartbeats do
        let originalEnv ← getEnv
        Competitor.activate (mode == "hammer" || isOptional)
        if mode == "stock" then
          let (_, body) ← g.intros
          body.withContext do
            if (← LibrarySearch.librarySearch body).isSome then throwError "library search did not close"
        else if mode == "hammer" then
          let seconds := max 1 (s.maxMillis / 1000)
          let code := "hammer {wallclockTimeout := " ++ toString seconds ++
            ", solverLongTimeout := " ++ toString seconds ++ "}"
          let remaining ← withOptions (·.set `premiseSelection.apiBaseUrl s.premiseApiBaseUrl) <|
            Finish.runCode g code s.maxHeartbeats
          unless remaining.isEmpty do throwError "hammer left goals"
        else if isOptional then
          let runner ← OptionalFinisher.getRunner
            (if isPlannedOptional then `JevPlannedHammerBackend.run else `JevHammerBackend.run)
          let ranker := if mode.endsWith "_jev" then some (cachedRanker s site extra true) else none
          withOptions (·.set `premiseSelection.apiBaseUrl s.premiseApiBaseUrl) <|
            runner g mode {
              maxMillis := s.maxMillis, maxHeartbeats := s.maxHeartbeats,
              maxDepth := depth, maxNodes := s.maxNodes, maxCalls := s.maxCalls,
              maxCandidates := s.maxCandidates } ranker optionalStats
        else if isFinish then
          if isPlanned then
            let name := ((mode.splitOn "_").drop 1).head!
            let ranker := if mode.endsWith "_jev" then some (cachedRanker s site extra true) else none
            Planned.solve [g] { Planned.experimentConfig name with
              maxDepth := depth, maxNodes := s.maxNodes,
              maxMillis := s.maxMillis, maxCalls := s.maxCalls, maxCandidates := s.maxCandidates }
              ranker plannedStats
          else if isAdvanced then
            let name := ((mode.splitOn "_").drop 1).head!
            let ranker := if mode.endsWith "_jev" then some (cachedRanker s site extra true) else none
            Advanced.solve [g] { Advanced.experimentConfig name with
              maxDepth := depth, maxNodes := s.maxNodes,
              maxMillis := s.maxMillis, maxCalls := s.maxCalls, maxCandidates := s.maxCandidates }
              ranker advancedStats
          else if mode == "aesop" || mode == "grind" then
            let code := if mode == "aesop" then "aesop (config := { maxRuleApplications := 120 })"
              else "grind (gen := 8)"
            let remaining ← Finish.runCode g code s.maxHeartbeats
            unless remaining.isEmpty do throwError "baseline left goals"
          else
            let strategy := (mode.splitOn "_").head!
            let ranker := if mode.endsWith "_jev" then some (cachedRanker s site extra true) else none
            Finish.solve [g] {
              strategy, independentScores := (mode.splitOn "_").contains "noul",
              maxDepth := depth, maxNodes := s.maxNodes,
              maxMillis := s.maxMillis, maxCalls := s.maxCalls, maxCandidates := s.maxCandidates }
              ranker finishStats
        else
          let cfg : Search.Config := {
            maxDepth := depth, maxNodes := s.maxNodes, maxTrials := s.maxTrials,
            maxCandidates := s.maxCandidates, maxCalls := s.maxCalls, maxMillis := s.maxMillis }
          let ranker := if mode == "jev" then some (cachedRanker s site extra) else none
          Search.solve [g] cfg ranker stats
        let p ← instantiateMVars (.mvar g)
        if p.hasExprMVar || p.hasSorry then throwError "incomplete proof"
        -- Check both well-typedness and the target; the source proof is never an oracle.
        unless ← isDefEq (← inferType p) (← g.getType) do throwError "wrong proof type"
        let closed ← Finish.inlineAuxiliaries originalEnv (← Search.kernelCheckClosure p)
        let closed ← Certificate.normalizeBinderAnnotations closed
        let closed ← withEnv originalEnv <| Search.kernelCheckClosure closed
        let cert ← withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.universes true
            |>.setBool `pp.fullNames true |>.setBool `pp.notation false
            |>.setBool `pp.explicit true |>.setBool `pp.proofs true) do
          let ty ← Certificate.normalizeBinderAnnotations (← inferType closed)
          return Json.mkObj [("expr", Certificate.encode closed ty),
            ("proof", toJson (← ppExpr closed).pretty),
            ("type", toJson (← ppExpr ty).pretty),
            ("universes", toJson ((collectLevelParams {} closed).params.map (·.toString)))]
        return ((← ppExpr p).pretty, p.getUsedConstants.map (·.toString), cert)
    proof := result.1
    used := result.2.1
    certificate := result.2.2
    solved := true
  catch e => message := (← e.toMessageData.toString)
  let elapsed := (← IO.monoMsNow) - start
  let external ← extra.get
  let statsJson ← if mode == "hammer" then pure (toJson (← Competitor.stats.get))
    else if isOptional then optionalStats.get
    else if isPlanned then pure (toJson (← plannedStats.get))
    else if isAdvanced then pure (toJson (← advancedStats.get))
    else if isFinish then pure (toJson (← finishStats.get)) else pure (toJson (← stats.get))
  appendJson s "trials.jsonl" <| Json.mkObj [
    ("site", toJson site), ("module", toJson s.moduleName), ("mode", toJson mode),
    ("depth", toJson depth), ("solved", toJson solved), ("elapsedMs", toJson elapsed),
    ("stats", statsJson), ("external", toJson external),
    ("censored", toJson external.blocked), ("error", toJson message),
    ("proof", toJson proof), ("constants", toJson used), ("certificate", certificate)]

end Bench.AtEachStep

register_option linter.tacticAnalysis.jevPilot : Bool := { defValue := false }

namespace Bench.AtEachStep
open Lean Meta Elab Command JevPilot

/-- Same Config hook and single-goal eligibility as mathlib's tryAtEachStep, augmented
with discovery, fixed manifest selection, explicit failures, and a paired depth sweep. -/
@[tacticAnalysis linter.tacticAnalysis.jevPilot]
def pass : Mathlib.TacticAnalysis.Config where
  run seq := do
    let some s ← settings | return
    for i in seq do
      let [goal] := i.tacI.goalsBefore | continue
      if i.mayFail then continue
      let some pos := i.tacI.stx.getPos? | continue
      let some tail := i.tacI.stx.getTailPos? | continue
      let ctx := { i.ctxI with mctx := i.tacI.mctxBefore }
      let gdecl := i.tacI.mctxBefore.decls.find! goal
      let goalPP ← ctx.runMetaM gdecl.lctx do
        withOptions (·.setBool `pp.mvars false) do return (← ppGoal goal).pretty
      let site := s!"{s.moduleName}:{pos.byteIdx}:{tail.byteIdx}:{hash goalPP}"
      if (← seen.get).contains site then continue
      seen.modify (·.insert site)
      let sourcePos := i.ctxI.fileMap.toPosition pos
      let parent := i.ctxI.parentDecl?.getD .anonymous
      let before? ← previousEnvironment.get
      let before := before?.getD i.ctxI.env
      let parentVisible := !parent.isAnonymous && before.contains parent
      -- Internal auxiliary constants created within this command may legitimately
      -- occur in a goal. Skip those contexts rather than silently changing their meaning.
      let contextAvailable ← ctx.runMetaM gdecl.lctx do
        let mut expressions := #[gdecl.type]
        for d in gdecl.lctx do
          expressions := expressions.push d.type
          if let some v := d.value? then expressions := expressions.push v
        let mut available := before?.isSome
        for e in expressions do
          for n in (← instantiateMVars e).getUsedConstants do
            available := available && before.contains n
        return available
      let safeNode := { i with ctxI := { i.ctxI with env := before } }
      let record := Json.mkObj [
        ("site", toJson site), ("module", toJson s.moduleName),
        ("byteStart", toJson pos.byteIdx), ("byteEnd", toJson tail.byteIdx),
        ("line", toJson sourcePos.line), ("column", toJson sourcePos.column),
        ("originalLine", toJson (sourcePos.line - s.injectedLines)),
        ("originalByteStart", toJson (pos.byteIdx - s.injectedBytes)),
        ("originalByteEnd", toJson (tail.byteIdx - s.injectedBytes)),
        ("declaration", toJson parent.toString), ("parentVisible", toJson parentVisible),
        ("originalParentVisible", toJson (!parent.isAnonymous && i.ctxI.env.contains parent)),
        ("contextAvailable", toJson contextAvailable), ("snapshotAvailable", toJson before?.isSome),
        ("goal", toJson goalPP), ("original", toJson (i.tacI.stx.reprint.getD "")),
        ("originalCloses", toJson i.tacI.goalsAfter.isEmpty)]
      if s.phase == "discover" then
        appendJson s "discovery.jsonl" record
      else if s.phase == "run" && s.sites.contains site then
        appendJson s "visited.jsonl" record
        if parentVisible || !contextAvailable then
          throwError "benchmark context/leakage guard failed for {parent}"
        -- Imported-tree construction is not charged only to whichever variant runs first.
        -- It uses the same safe environment. Per-goal local retrieval remains timed.
        unless ← warmed.get do
          let warmupStart ← IO.monoMsNow
          let _ ← safeNode.ctxI.runTactic i.tacI goal fun _ =>
            Search.withHeartbeatBudget 0 do
              discard <| LibrarySearch.libSearchFindDecls (mkConst ``True)
              if s.modes.any (fun mode => mode.startsWith "v2_" || mode.startsWith "v3_" || mode.startsWith "hammer_" ||
                  mode.startsWith "neural_" || mode.startsWith "planned_") then
                discard <| LibrarySuggestions.SineQuaNon.sineQuaNonTheorems ``True
                Retrieval.warm
          let nativeWarmupMs := (← IO.monoMsNow) - warmupStart
          let hammerWarmupStart ← IO.monoMsNow
          if s.warmHammerImports && s.modes.any (fun mode =>
              mode == "hammer" || mode.startsWith "hammer_" || mode.startsWith "neural_" || mode.startsWith "planned_") then
            let _ ← safeNode.ctxI.runTactic i.tacI goal fun _ =>
              Search.withHeartbeatBudget 0 <| Competitor.warmImports s.premiseApiBaseUrl
          appendJson s "warmup.jsonl" (Json.mkObj [("module", toJson s.moduleName),
            ("nativeImportedIndexWarmupMs", toJson nativeWarmupMs),
            ("hammerImportedWarmupMs", toJson ((← IO.monoMsNow) - hammerWarmupStart)),
            ("importedIndexWarmupMs", toJson ((← IO.monoMsNow) - warmupStart))])
          warmed.set true
        -- Always try all depths independently; report cumulative unions separately.
        let modes := if s.rotateModes then
          s.modes.qsort (fun a b =>
            let ha := hash (site ++ ":" ++ a)
            let hb := hash (site ++ ":" ++ b)
            if ha == hb then a < b else ha < hb)
          else s.modes
        for mode in modes do
          if mode == "stock" then runTrial s safeNode goal site mode 6
          else
            for depth in s.depths do runTrial s safeNode goal site mode depth

/-- Registered after Mathlib's tacticAnalysis linter: our pass sees the environment
from the preceding command. Synchronous elaboration is required by the driver.
This also excludes current-command auxiliary theorems, not just the parent name. -/
initialize addLinter {
  name := `Bench.AtEachStep.captureEnvironment
  run := fun _ => do
    if (← settings).isSome then
      previousEnvironment.set (some (← getEnv)) }

end Bench.AtEachStep
