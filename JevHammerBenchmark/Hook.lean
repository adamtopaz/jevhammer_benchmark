module

public meta import JevHammerBenchmark.Methods
public meta import JevHammerBenchmark.Ranker
public meta import JevHammerBenchmark.Certificate
public meta import Mathlib.Tactic.TacticAnalysis.Declarations

public meta section
namespace JevHammerBenchmark
open Lean Meta Elab Command

structure Settings where
  phase : String
  moduleName : String
  outputDir : String
  injectedBytes : Nat
  sites : Array String := #[]
  owners : Array String := #[]
  methods : Array String := #[]
  overrides : Json := Json.mkObj []
  mock : Bool := true
  maxRequests : Nat := 0
  maxInputTokens : Nat := 0
  outerHeartbeats : Nat := 200000
  certificates : String := ""
  deriving FromJson, ToJson

initialize settingsRef : IO.Ref (Option Settings) ← IO.mkRef none
initialize seen : IO.Ref (Std.HashSet String) ← IO.mkRef {}
initialize beforeCommand : IO.Ref (Option Environment) ← IO.mkRef none
initialize warmed : IO.Ref (Std.HashSet String) ← IO.mkRef {}

private def settings : IO (Option Settings) := do
  if let some s ← settingsRef.get then return some s
  let some path ← IO.getEnv "JEVHAMMER_BENCH_CONFIG" | return none
  let s ← IO.ofExcept (Json.parse (← IO.FS.readFile path) >>= fromJson?)
  settingsRef.set (some s)
  return some s

private def record (s : Settings) (file : String) (json : Json) : IO Unit :=
  appendJson (System.FilePath.mk s.outputDir / file) json

private def closeProof (original : Environment) (goal : MVarId) : MetaM Json := goal.withContext do
  let proof ← instantiateMVars (.mvar goal)
  unless ← isDefEq (← inferType proof) (← goal.getType) do throwError "wrong proof type"
  -- Abstract ALL locals so replay can match the original source goal exactly,
  -- even when the successful proof only uses some of its hypotheses.
  let proof ← instantiateMVars (← mkLambdaFVars (← getLCtx).getFVars proof)
  if proof.hasExprMVar || proof.hasFVar || proof.hasSorry then throwError "incomplete proof"
  let used := (collectLevelParams {} proof).params
  let proof := ((← getMCtx).levelMVarToParam used.contains (fun _ => false)
    proof `_jevBenchU).expr
  let proof ← JevHammer.inlineAuxiliaries original proof
  withEnv original do
    discard <| JevHammer.kernelCheckClosure proof
    return Certificate.encode proof (← inferType proof)

private def replay (s : Settings) (node : Mathlib.TacticAnalysis.TacticNode)
    (site owner : String) : CommandElabM Unit := do
  let rows ← IO.ofExcept (Json.parse (← IO.FS.readFile s.certificates) >>= Json.getArr?)
  for row in rows do
    unless row.getObjValD "site" == toJson site do continue
    let mut error := ""
    try
      let goal :: _ := node.tacI.goalsBefore | throwError "empty source goal list"
      let ctx := { node.ctxI with mctx := node.tacI.mctxBefore }
      let some decl := node.tacI.mctxBefore.decls.find? goal | throwError "missing goal"
      ctx.runMetaM decl.lctx do
        let certificates ← ofExcept (row.getObjValD "certificates").getArr?
        unless certificates.size == node.tacI.goalsBefore.length do
          throwError "certificate goal count differs from the source"
        for (goal, certificate) in node.tacI.goalsBefore.zip certificates.toList do
          Certificate.assign certificate goal owner
    catch e => error ← e.toMessageData.toString
    record s "replay.jsonl" <| Json.mkObj [
      ("site", toJson site), ("method", row.getObjValD "method"),
      ("verified", toJson error.isEmpty), ("error", toJson error)]

private def trial (s : Settings) (node : Mathlib.TacticAnalysis.TacticNode)
    (site owner methodName : String) : CommandElabM Unit := do
  let goal :: _ := node.tacI.goalsBefore | throwError "empty source goal list"
  let ctx := { node.ctxI with mctx := node.tacI.mctxBefore }
  let some decl := node.tacI.mctxBefore.decls.find? goal | throwError "missing goal"
  -- Admission and goal-independent warmup are outside the trial clock.
  let method ← ctx.runMetaM decl.lctx do
    let method ← loadMethod methodName
    let config ← ofExcept <| fromJson? ((toJson method.config).mergeObj s.overrides)
    return { method with config }
  unless (← warmed.get).contains methodName do
    let start ← IO.monoMsNow
    let provenance ← ctx.runMetaM {} <| method.runWarmup (s.owners.map String.toName)
    record s "warmup.jsonl" <| (methodInfo methodName method).mergeObj <| Json.mkObj [
      ("module", toJson s.moduleName), ("elapsedMs", toJson ((← IO.monoMsNow) - start)),
      ("provenance", provenance)]
    warmed.modify (·.insert methodName)
  let stats ← IO.mkRef ({} : JevHammer.Stats)
  let blocked ← IO.mkRef false
  let start ← IO.monoMsNow
  let mut error := ""
  let mut certificates := #[]
  try
    certificates ← ctx.runMetaM decl.lctx do
      JevHammer.withHeartbeatBudget s.outerHeartbeats do
        let original ← getEnv
        let ranker ← budgetedRanker s.outputDir site methodName method.config
          s.maxRequests s.maxInputTokens s.mock blocked
        JevHammer.solve node.tacI.goalsBefore method.selector ranker stats
          method.config method.tactics
        node.tacI.goalsBefore.toArray.mapM (closeProof original)
  catch e => error ← e.toMessageData.toString
  let elapsed := (← IO.monoMsNow) - start
  record s "trials.jsonl" <| (methodInfo methodName method).mergeObj <| Json.mkObj [
    ("schema", toJson (1 : Nat)), ("site", toJson site), ("declaration", toJson owner),
    ("module", toJson s.moduleName), ("method", toJson methodName),
    ("solved", toJson error.isEmpty),
    ("onTime", toJson (error.isEmpty && elapsed <= method.config.maxMillis)),
    ("elapsedMs", toJson elapsed), ("guidance", toJson (if s.mock then "mock" else "jev")),
    ("budgetBlocked", toJson (← blocked.get)),
    ("error", toJson error), ("stats", toJson (← stats.get)),
    ("certificates", .arr certificates)]

end JevHammerBenchmark

register_option linter.tacticAnalysis.jevHammerBenchmark : Bool := { defValue := false }

namespace JevHammerBenchmark
open Lean Meta Elab Command

@[tacticAnalysis linter.tacticAnalysis.jevHammerBenchmark]
def pass : Mathlib.TacticAnalysis.Config where
  run seq := do
    let some s ← settings | return
    for node in seq do
      if node.mayFail || node.tacI.goalsBefore.isEmpty then continue
      let some pos := node.tacI.stx.getPos? | continue
      let some tail := node.tacI.stx.getTailPos? | continue
      let some first := node.tacI.goalsBefore.head? | continue
      let some decl := node.tacI.mctxBefore.decls.find? first | continue
      let ctx := { node.ctxI with mctx := node.tacI.mctxBefore }
      let goalText ← ctx.runMetaM decl.lctx do
        withOptions (·.setBool `pp.mvars false) do
          return String.intercalate "\n---\n" (← node.tacI.goalsBefore.mapM fun g =>
            g.withContext do return (← ppGoal g).pretty)
      let start := pos.byteIdx - s.injectedBytes
      let stop := tail.byteIdx - s.injectedBytes
      let site := s!"{s.moduleName}:{start}:{stop}:{hash goalText}"
      if (← seen.get).contains site then continue
      seen.modify (·.insert site)
      let parent := node.ctxI.parentDecl?.getD .anonymous
      -- `example` uses a synthetic `_example` parent, not Name.anonymous.
      -- Require an owner that survives the completed command so declaration
      -- grouping and preparation exclusions have an actual constant identity.
      -- The completed environment is used ONLY for this identity check; search
      -- and certificate replay still receive the preceding-command environment.
      let ownerAvailable := !parent.isAnonymous && (← getEnv).contains parent
      let before? ← beforeCommand.get
      let before := before?.getD node.ctxI.env
      let available ← ctx.runMetaM decl.lctx do
        let mut ok := before?.isSome && ownerAvailable && !before.contains parent
        for goal in node.tacI.goalsBefore do
          let goalAvailable ← goal.withContext do
            let mut expressions := #[(← goal.getType)]
            for localDecl in ← getLCtx do
              expressions := expressions.push localDecl.type
              if let some value := localDecl.value? then expressions := expressions.push value
            let mut available := true
            for e in expressions do
              for name in (← instantiateMVars e).getUsedConstants do
                available := available && before.contains name
            return available
          ok := ok && goalAvailable
        return ok
      let info := Json.mkObj [
        ("site", toJson site), ("module", toJson s.moduleName),
        ("byteStart", toJson start), ("byteEnd", toJson stop),
        ("declaration", toJson parent.toString), ("goal", toJson goalText),
        ("goalCount", toJson node.tacI.goalsBefore.length), ("eligible", toJson available)]
      if s.phase == "discover" then record s "discovery.jsonl" info
      else if s.sites.contains site then
        unless available do throwError "unsafe or changed source context at {site}"
        record s "visited.jsonl" info
        let safeNode := { node with ctxI := { node.ctxI with env := before } }
        if s.phase == "replay" then replay s safeNode site parent.toString
        else
          -- Rotate order deterministically to avoid always giving the same arm
          -- the first access to shared runtime caches.
          let methods := s.methods.qsort fun a b =>
            let x := hash (site ++ a)
            let y := hash (site ++ b)
            if x == y then a < b else x < y
          for method in methods do trial s safeNode site parent.toString method

/-- Registered after tacticAnalysis: it retains the preceding command's
environment, excluding the completed target and its generated auxiliaries. -/
initialize addLinter {
  name := `JevHammerBenchmark.captureEnvironment
  run := fun _ => do
    if (← settings).isSome then beforeCommand.set (some (← getEnv)) }

end JevHammerBenchmark
