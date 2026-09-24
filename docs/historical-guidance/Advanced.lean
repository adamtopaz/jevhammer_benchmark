module

public meta import JevFinish
public meta import Lean.LibrarySuggestions.SineQuaNon
public meta import JevFinish.Scoring
public meta import JevFinish.Selection
public meta import JevFinish.Retrieval
public meta import Aesop
public meta import Mathlib.Tactic.Contrapose
public meta import Lean.Elab.Tactic
public meta import Lean.Elab.Tactic.Meta
public meta import Lean.Elab.ConfigEval

public meta section

/-! Experimental successor to the frozen baseline. General-purpose, proof-producing finishers. Jev selects from Lean-generated
premises and checked successor states. No model-produced code is executed. -/
namespace JevPilot.Advanced
open Lean Meta Elab

structure Config where
  maxNodes : Nat := 16
  maxDepth : Nat := 3
  beamWidth : Nat := 4
  maxCandidates : Nat := 24
  maxPremises : Nat := 64
  premiseCount : Nat := 8
  independentScores : Bool := false
  /-- Baseline scan, indexed SInE + local/conclusion routes, or their union. -/
  retrieval : String := "baseline"
  diverseActions : Bool := false
  independentContinuations : Bool := false
  preserveStructural : Bool := false
  complementary : Bool := false
  roleSelection : Bool := false
  refreshPremises : Bool := false
  solverProfile : String := "baseline"
  maxCalls : Nat := 3
  maxMillis : Nat := 8000
  tacticHeartbeats : Nat := 15000
  /-- `premise`, `lookahead`, or their combination `hybrid`. -/
  strategy : String := "hybrid"
  deriving Repr

/-- Named ablations are fixed before a measured run; the frozen baseline stays separate. -/
def experimentConfig (name : String) : Config :=
  let base : Config := { independentScores := true }
  match name with
  | "control" => base
  | "sine" => { base with retrieval := "sine" }
  | "mixed" => { base with retrieval := "mixed" }
  | "broad" => { base with retrieval := "mixed", maxPremises := 128 }
  | "diverse" => { base with diverseActions := true }
  | "states" => { base with independentContinuations := true }
  | "guard" => { base with preserveStructural := true }
  | "combo" => { base with
      retrieval := "mixed"
      diverseActions := true
      independentContinuations := true
      preserveStructural := true }
  | "index" => { base with retrieval := "index" }
  | "superset" => { base with retrieval := "superset", maxPremises := 128 }
  | "complement" => { base with retrieval := "superset", maxPremises := 128, complementary := true }
  | "roles" => { base with retrieval := "superset", maxPremises := 128, roleSelection := true }
  | "refresh" => { base with retrieval := "index", refreshPremises := true }
  | "solvers" => { base with retrieval := "index", solverProfile := "standard" }
  | "try" => { base with strategy := "portfolio", solverProfile := "try" }
  | "next" => { base with
      retrieval := "superset"
      maxPremises := 128
      diverseActions := true
      complementary := true
      solverProfile := "standard" }
  | "adaptive" => { base with retrieval := "index", diverseActions := true, refreshPremises := true }
  | "adaptiveplus" => { base with
      retrieval := "index"
      diverseActions := true
      refreshPremises := true
      solverProfile := "standard" }
  | _ => base

structure Stats where
  nodes : Nat := 0
  trials : Nat := 0
  rankCalls : Nat := 0
  rankFailures : Nat := 0
  inputTokens : Nat := 0
  outputTokens : Nat := 0
  elapsedMs : Nat := 0
  exhausted : Bool := false
  model : String := ""
  premises : Nat := 0
  branches : Nat := 0
  winner : String := ""
  retrievalMs : Nat := 0
  refreshes : Nat := 0
  deriving Repr, ToJson

/-- Shared by the experiment's recorded/cached ranker and the public live tactics. -/
def rankingRequest (state : Json) (choices : Array Json) (model := "jev-1.13.0") : TypeSafe.Request :=
  if state.getObjValD "selection_profile" == .str Selection.profile then
    Selection.request state choices model
  else Finish.Scoring.request state choices model

def responseRanking (response : TypeSafe.Response) (size : Nat) (independent := false) : IO Search.Ranking :=
  Finish.Scoring.ranking response size independent

def jevRanker (client : TypeSafe.Client) : Search.Ranker := fun state choices => do
  responseRanking (← client.systemOneIO (rankingRequest state choices)) choices.size
    (state.getObjValD "independent_scores" == .bool true)

abbrev inlineAuxiliaries := Finish.inlineAuxiliaries

private def goalView (g : MVarId) : MetaM Json := g.withContext do
  withOptions (·.setBool `pp.mvars false) do
    let mut context := #[]
    for d in ← getLCtx do
      unless d.isImplementationDetail do
        let value ← match d.value? with
          | some v => pure (toJson (← ppExpr (← instantiateMVars v)).pretty)
          | none => pure Json.null
        context := context.push <| Json.mkObj [("name", toJson d.userName.toString),
          ("type", toJson (← ppExpr (← instantiateMVars d.type)).pretty), ("value", value)]
    return Json.mkObj [("target", toJson (← ppExpr (← instantiateMVars (← g.getType))).pretty),
      ("context", .arr context)]

abbrev runCode := Finish.runCode

private structure Runtime where
  config : Config
  ranker : Option Search.Ranker
  stats : IO.Ref Stats
  start : Nat
  retriever : Option (MVarId → Nat → MetaM (Array Name)) := none

private def Runtime.check (rt : Runtime) : MetaM Unit := do
  if (← IO.monoMsNow) - rt.start >= rt.config.maxMillis then
    rt.stats.modify fun s => { s with exhausted := true }
    throwError "Jev finish wall budget exhausted"

private def Runtime.rank (rt : Runtime) (state : Json) (choices : Array Json) : MetaM (Array Nat) := do
  let fallback := (List.range choices.size).toArray
  if choices.size < 2 then return fallback
  let some ranker := rt.ranker | return fallback
  if (← rt.stats.get).rankCalls >= rt.config.maxCalls then return fallback
  rt.check
  rt.stats.modify fun s => { s with rankCalls := s.rankCalls + 1 }
  try
    let r ← ranker state choices
    unless Search.isPermutation r.order choices.size do throwError "invalid Jev ranking"
    rt.stats.modify fun s => { s with
      inputTokens := s.inputTokens + r.usage.inputTokens.getD 0
      outputTokens := s.outputTokens + r.usage.outputTokens.getD 0
      model := r.model }
    return r.order
  catch _ =>
    rt.stats.modify fun s => { s with rankFailures := s.rankFailures + 1 }
    return fallback

private def Runtime.tryCode (rt : Runtime) (g : MVarId) (code : String)
    (close : Bool := false) : MetaM (Option (List MVarId)) := do
  let _ : MonadExceptOf Exception MetaM :=
    { (inferInstance : MonadExceptOf Exception MetaM) with tryCatch := tryCatchRuntimeEx }
  rt.check
  let saved ← saveState
  rt.stats.modify fun s => { s with trials := s.trials + 1 }
  try
    let gs ← runCode g code rt.config.tacticHeartbeats
    if close && !gs.isEmpty then
      saved.restore
      return none
    return some gs
  catch _ =>
    saved.restore
    return none

/-- Strong deterministic control; also the common prefix of every new finisher. -/
abbrev portfolioCodes := Finish.portfolioCodes

/-- These names are parsed only in the actual source environment. No imports of
completed target modules are added to make a particular solver available. -/
def extraSolverCodes : Array String := #["norm_num", "ring_nf", "linarith", "nlinarith",
  "positivity", "fun_prop", "continuity", "measurability", "tauto", "decide"]

private def discharge (rt : Runtime) (g : MVarId) (root := false) : MetaM Bool := do
  let codes := portfolioCodes ++ if !root then #[] else
    if rt.config.solverProfile == "standard" then extraSolverCodes
    else if rt.config.solverProfile == "try" then #["try?"] else #[]
  for code in codes do
    if (← rt.tryCode g code true).isSome then
      rt.stats.modify fun s => { s with winner := code }
      return true
  return false

private def relevantSymbol (n : Name) : Bool :=
  !([``Eq, ``Iff, ``And, ``Or, ``Not, ``Exists, ``True, ``False, ``Decidable,
     ``OfNat.ofNat, ``OfNat, ``Nat, ``Int].contains n) &&
  !n.isInternal && !n.toString.startsWith "Lean." && !n.toString.startsWith "JevPilot."

private structure Premise where
  name : Name
  weight : Nat

/-- Symbol-overlap retrieval complements conclusion-indexed library search. It can
find rewrite/forward lemmas even when their conclusion does not unify with the goal.
The actual current environment is scanned, so no later declaration can leak in. -/
private def retrieveBaseline (g : MVarId) (limit : Nat) : MetaM (Array Name) := g.withContext do
  let target ← instantiateMVars (← g.getType)
  let mut targetSymbols := target.getUsedConstants.filter relevantSymbol
  let mut contextSymbols : Array Name := #[]
  for h in ← getLCtx do
    unless h.isImplementationDetail do
      contextSymbols := contextSymbols ++ ((← instantiateMVars h.type).getUsedConstants.filter relevantSymbol)
  targetSymbols := targetSymbols ++ contextSymbols
  let mut candidates : Array Premise := #[]
  for (n, info) in (← getEnv).constants.toList do
    unless info.isTheorem && !n.isInternal do continue
    let symbols := info.type.getUsedConstants
    let overlap := targetSymbols.foldl (fun s c => s + if symbols.contains c then 1 else 0) 0
    if overlap == 0 then continue
    let weight := 1000 * overlap / (symbols.size + 4)
    candidates := candidates.push { name := n, weight }
  candidates := candidates.qsort fun a b =>
    if a.weight == b.weight then a.name.toString < b.name.toString else a.weight > b.weight
  let direct ← LibrarySearch.libSearchFindDecls target
  let mut result : Array Name := #[]
  -- Reserve most of the shortlist for semantic symbol retrieval, rather than
  -- drowning it in generic conclusion matches.
  for (n, _) in direct.take (limit / 4) do
    unless result.contains n do result := result.push n
  for p in candidates do
    if result.size >= limit then break
    unless result.contains p.name do result := result.push p.name
  return result

/-- Round-robin selection prevents one retrieval or action route from filling the cap. -/
def interleaveUnique (routes : Array (Array String)) (limit : Nat) : Array String := Id.run do
  let mut result := #[]
  let depth := routes.foldl (fun n r => max n r.size) 0
  for i in [:depth] do
    for route in routes do
      if result.size >= limit then return result
      if let some item := route[i]? then
        unless result.contains item do result := result.push item
  return result

def retrieve (g : MVarId) (limit : Nat) (method : String) : MetaM (Array Name) := g.withContext do
  if method == "baseline" then return ← retrieveBaseline g limit
  if method == "index" then return ← Retrieval.retrieve g limit
  let target ← instantiateMVars (← g.getType)
  let sine ← LibrarySuggestions.sineQuaNonSelector 1.5 g { maxSuggestions := limit * 2 }
  let localFacts ← LibrarySuggestions.currentFile g { maxSuggestions := limit }
  let direct ← LibrarySearch.libSearchFindDecls target
  let mut routes := #[sine.map (·.name), direct.map (·.1), localFacts.map (·.name)]
  if method == "mixed" then routes := routes.push (← retrieveBaseline g limit)
  -- Keep the original 64 candidates in exactly their original order. The second
  -- half adds alternatives; it cannot evict a baseline candidate before scoring.
  let mut result ← if method == "superset" then Retrieval.retrieve g (min 64 limit) else pure #[]
  let env ← getEnv
  let depth := routes.foldl (fun n r => max n r.size) 0
  for i in [:depth] do
    for route in routes do
      if result.size >= limit then return result
      if let some n := route[i]? then
        -- The current snapshot is authoritative even if an upstream index is cached.
        if !n.isInternal && !result.contains n then
          if let some info := env.find? n then
            if info.isTheorem then result := result.push n
  return result

private def premiseViews (names : Array Name) : MetaM (Array Json) := names.mapM fun n => do
  return Json.mkObj [("lemma", toJson n.toString), ("type", toJson (← ppExpr (← getConstInfo n).type).pretty)]

private def rankPremises (rt : Runtime) (g : MVarId) (previous : Array Name := #[]) : MetaM (Array Name) := g.withContext do
  let start ← IO.monoMsNow
  let names ← match rt.retriever with
    | some retriever => retriever g rt.config.maxPremises
    | none => retrieve g rt.config.maxPremises rt.config.retrieval
  let elapsed := (← IO.monoMsNow) - start
  rt.stats.modify fun s => { s with
    premises := s.premises + names.size
    retrievalMs := s.retrievalMs + elapsed }
  let choices ← premiseViews names
  let goal ← goalView g
  let oldViews ← premiseViews previous
  let state := if previous.isEmpty then
    Json.mkObj [("task", .str "premises"), ("independent_scores", toJson rt.config.independentScores),
      ("goal", goal)]
    else Json.mkObj [("task", .str "premise_refresh"), ("independent_scores", .bool true),
      ("selection_profile", .str Selection.profile), ("previous_premises", .arr oldViews),
      ("goal", goal)]
  let order ← rt.rank state choices
  return order.filterMap (names[·]?)

private def premiseFinish (rt : Runtime) (g : MVarId) (names : Array Name) : MetaM Bool := do
  for count in #[rt.config.premiseCount, rt.config.premiseCount * 2] do
    let ns := names.take count
    unless ns.isEmpty do
      let args := String.intercalate ", " (ns.toList.map (·.toString))
      for code in #[s!"solve | simp_all [{args}]", s!"grind (gen := 8) [{args}]",
          s!"aesop (add unsafe 50% {String.intercalate " " (ns.toList.map (·.toString))})" ++ " (config := { maxRuleApplications := 160 })"] do
        if (← rt.tryCode g code true).isSome then
          rt.stats.modify fun s => { s with winner := code }
          return true
  return false

private def refinePremises (rt : Runtime) (g : MVarId) (names : Array Name) : MetaM (Bool × Array Name) := g.withContext do
  if (← rt.stats.get).rankCalls >= rt.config.maxCalls then return (false, names)
  if rt.config.complementary then
    let selected := names.take rt.config.premiseCount
    let alternatives := names.drop rt.config.premiseCount
    let state := Json.mkObj [("task", .str "premise_complement"), ("independent_scores", .bool true),
      ("selection_profile", .str Selection.profile), ("goal", ← goalView g),
      ("already_selected", .arr (← premiseViews selected)),
      ("failed_automation", .str "simp_all, grind, aesop"),
      ("failed_prefix_sizes", toJson #[rt.config.premiseCount, rt.config.premiseCount * 2])]
    let order ← rt.rank state (← premiseViews alternatives)
    let reordered := selected ++ order.filterMap (alternatives[·]?)
    return (← premiseFinish rt g reordered, reordered)
  if rt.config.roleSelection then
    let mut candidates : Array (Name × Selection.Role) := #[]
    let mut choices := #[]
    for name in names.take 32 do
      for role in #[Selection.Role.rewrite, .forward, .backward] do
        candidates := candidates.push (name, role)
        choices := choices.push <| Json.mkObj [("lemma", toJson name.toString),
          ("type", toJson (← ppExpr (← getConstInfo name).type).pretty), ("role", .str role.label)]
    let state := Json.mkObj [("task", .str "premise_roles"), ("independent_scores", .bool true),
      ("selection_profile", .str Selection.profile), ("goal", ← goalView g)]
    let order ← rt.rank state choices
    let sets := Selection.roleSets candidates order rt.config.premiseCount
    let args := fun ns => String.intercalate ", " ((ns : Array Name).toList.map (·.toString))
    let codes := #[s!"solve | simp_all [{args sets.rewrite}]", s!"grind (gen := 8) [{args sets.forward}]",
      s!"aesop (add unsafe 50% {String.intercalate " " (sets.backward.toList.map (·.toString))})" ++
        " (config := { maxRuleApplications := 160 })"]
    for code in codes do
      if (← rt.tryCode g code true).isSome then
        rt.stats.modify fun s => { s with winner := code }
        return (true, names)
    return (false, sets.backward ++ names.filter (!sets.backward.contains ·))
  return (false, names)

private structure Branch where
  goals : List MVarId
  saved : Meta.SavedState
  path : Array String
  view : Json
  ancestors : Array String := #[]

private def branchView (gs : List MVarId) (path : Array String) : MetaM Json := do
  return Json.mkObj [("actions", toJson path), ("remaining", toJson (← gs.toArray.mapM goalView))]

private def actionCodes (g : MVarId) (premises : Array Name) (diverse : Bool) : MetaM (Array String) := g.withContext do
  let mut codes := #["simp_all", "intros", "constructor", "ext1", "contrapose!", "push_neg at *", "symm"]
  let basic := codes
  let mut definitions := #[]
  let mut localApply := #[]
  let mut localCases := #[]
  let mut localRewrite := #[]
  let mut lemmaApply := #[]
  let mut lemmaRewrite := #[]
  let mut lemmaSimp := #[]
  -- Selective definitional normalization is generated from expressions, not a
  -- hand-maintained list of mathematics-specific rewrite rules.
  let symbols := (← instantiateMVars (← g.getType)).getUsedConstants.filter relevantSymbol
  for n in symbols.take 8 do
    if (← getConstInfo n).isDefinition then
      let more := #[s!"unfold {n}", s!"simp_all only [{n}]"]
      codes := codes ++ more
      definitions := definitions ++ more
  let mut hypCount := 0
  for h in ← getLCtx do
    if h.isImplementationDetail || h.userName.isInternal || hypCount >= 8 then continue
    if ← isProp h.type then
      let id := h.userName.toString
      codes := codes ++ #[s!"apply {id}", s!"cases {id}", s!"rw [{id}]", s!"rw [← {id}]"]
      localApply := localApply.push s!"apply {id}"
      localCases := localCases.push s!"cases {id}"
      localRewrite := localRewrite ++ #[s!"rw [{id}]", s!"rw [← {id}]"]
      hypCount := hypCount + 1
  for n in premises.take 12 do
    codes := codes ++ #[s!"apply {n}", s!"rw [{n}]", s!"rw [← {n}]", s!"simp only [{n}] at *"]
    lemmaApply := lemmaApply.push s!"apply {n}"
    lemmaRewrite := lemmaRewrite ++ #[s!"rw [{n}]", s!"rw [← {n}]"]
    lemmaSimp := lemmaSimp.push s!"simp only [{n}] at *"
  if diverse then
    return interleaveUnique #[basic, lemmaApply, localApply, lemmaRewrite, definitions,
      localCases, lemmaSimp, localRewrite] codes.size
  return codes

private def expand (rt : Runtime) (b : Branch) (premises : Array Name) : MetaM (Array Branch) := do
  b.saved.restore
  let gs ← b.goals.filterM fun g => return !(← g.isAssigned)
  let g :: rest := gs | return #[b]
  let codes ← actionCodes g premises rt.config.diverseActions
  let mut branches : Array Branch := #[]
  let mut seen : Array String := #[]
  for code in codes do
    if branches.size >= rt.config.maxCandidates then break
    b.saved.restore
    if let some next ← rt.tryCode g code then
      -- Close obvious subgoals before asking the model; assignments remain in the
      -- same snapshot as every sibling, including shared existential witnesses.
      let mut pending : List MVarId := []
      for h in next ++ rest do
        unless ← h.isAssigned do
          if (← rt.tryCode h "solve | assumption | rfl | trivial" true).isNone then
            pending := pending ++ [h]
      let path := b.path.push code
      let view ← branchView pending path
      let key := (view.getObjValD "remaining").compress
      if key == (b.view.getObjValD "remaining").compress || b.ancestors.contains key then continue
      if seen.contains key then continue
      seen := seen.push key
      branches := branches.push {
        goals := pending, saved := ← saveState, path, view,
        ancestors := b.ancestors.push (b.view.getObjValD "remaining").compress }
      if pending.isEmpty then break
  rt.stats.modify fun s => { s with branches := s.branches + branches.size }
  b.saved.restore
  return branches

private def lookahead (rt : Runtime) (g : MVarId) (premises : Array Name) : MetaM Bool := do
  let initial : Branch := { goals := [g], saved := ← saveState, path := #[], view := ← branchView [g] #[] }
  let mut frontier := #[initial]
  for _ in [:rt.config.maxDepth] do
    let mut successors : Array Branch := #[]
    for b in frontier do
      if (← rt.stats.get).nodes >= rt.config.maxNodes then
        rt.stats.modify fun s => { s with exhausted := true }
        return false
      rt.stats.modify fun s => { s with nodes := s.nodes + 1 }
      b.saved.restore
      if !b.path.isEmpty then
        let mut allClosed := true
        for h in b.goals do
          unless ← h.isAssigned do
            unless ← discharge rt h do
              allClosed := false
              break
        if allClosed then
          rt.stats.modify fun s => { s with winner := String.intercalate "; " b.path.toList ++ "; portfolio" }
          return true
      -- Failed closures must not leave a partially solved branch committed.
      b.saved.restore
      let mut branchPremises := premises
      if rt.config.refreshPremises && !b.path.isEmpty &&
          (← rt.stats.get).refreshes == 0 && (← rt.stats.get).rankCalls < rt.config.maxCalls then
        if let some h := b.goals.head? then
          rt.stats.modify fun s => { s with refreshes := s.refreshes + 1 }
          branchPremises ← rankPremises rt h premises
          if ← premiseFinish rt h branchPremises then
            let mut allClosed := true
            for other in b.goals do
              unless ← other.isAssigned do
                unless ← discharge rt other do allClosed := false; break
            if allClosed then return true
          b.saved.restore
      let next ← expand rt b branchPremises
      for c in next do
        if c.goals.isEmpty then
          c.saved.restore
          rt.stats.modify fun s => { s with winner := String.intercalate "; " c.path.toList }
          return true
      successors := successors ++ next
    if successors.isEmpty then return false
    let mut state := [("task", .str "continuations"), ("goal", initial.view)]
    if rt.config.independentContinuations then state := state ++ [("independent_scores", .bool true)]
    let order ← rt.rank (Json.mkObj state)
      (successors.map (·.view))
    let mut selected := order.take rt.config.beamWidth
    if rt.config.preserveStructural && !selected.isEmpty && !selected.contains 0 then
      selected := (selected.take (selected.size - 1)).push 0
    frontier := selected.filterMap (successors[·]?)
  -- Discharge the last selected layer, too.
  for b in frontier do
    if (← rt.stats.get).nodes >= rt.config.maxNodes then
      rt.stats.modify fun s => { s with exhausted := true }
      return false
    rt.stats.modify fun s => { s with nodes := s.nodes + 1 }
    b.saved.restore
    let mut ok := true
    for h in b.goals do
      unless ← h.isAssigned do
        unless ← discharge rt h do
          ok := false
          break
    if ok then
      rt.stats.modify fun s => { s with winner := String.intercalate "; " b.path.toList ++ "; portfolio" }
      return true
  return false

/-- Atomic finishing API: closes every input goal with a kernel-checked term or
restores the original metavariable state. API failures only change search order. -/
def solve (goals : List MVarId) (config : Config := {}) (ranker : Option Search.Ranker := none)
    (stats : IO.Ref Stats) (retriever : Option (MVarId → Nat → MetaM (Array Name)) := none) : MetaM Unit := do
  let _ : MonadExceptOf Exception MetaM :=
    { (inferInstance : MonadExceptOf Exception MetaM) with tryCatch := tryCatchRuntimeEx }
  let initial ← saveState
  let start ← IO.monoMsNow
  let rt : Runtime := { config, ranker, stats, start, retriever }
  try
    for g in goals do
      if ← g.isAssigned then continue
      g.withContext do
        if ← discharge rt g true then pure ()
        else if config.strategy == "portfolio" then throwError "portfolio did not close"
        else
          let (_, g) ← g.intros
          let before ← saveState
          let mut premises ← rankPremises rt g
          let mut closed ← if config.strategy != "lookahead" then premiseFinish rt g premises else pure false
          if !closed && (config.complementary || config.roleSelection) then
            before.restore
            let result ← refinePremises rt g premises
            closed := result.1
            premises := result.2
          unless closed do
            before.restore
            if config.strategy == "premise" then throwError "premise finisher did not close"
            unless ← lookahead rt g premises do throwError "lookahead did not close"
    for g in goals do
      g.withContext do
        let p ← instantiateMVars (.mvar g)
        unless ← isDefEq (← inferType p) (← g.getType) do throwError "incorrect target"
        discard <| Search.kernelCheckClosure p
  catch e =>
    initial.restore
    throw e
  finally
    let elapsed := (← IO.monoMsNow) - start
    stats.modify fun s => { s with elapsedMs := elapsed }

end JevPilot.Advanced

namespace JevPilot.Advanced
open Lean Meta Elab Tactic

declare_config_elab elabAdvancedConfig Config

private def evalFinish (live usePass : Bool) (config : Config) : TacticM Unit := do
  let initial ← saveState
  let original ← getEnv
  let goals ← getGoals
  -- Decrypt/read credentials only if cheap deterministic automation fails and a
  -- ranking is actually needed. Clients are reused within this tactic invocation.
  let clientRef ← IO.mkRef (none : Option TypeSafe.Client)
  let ranker : Search.Ranker := fun state choices => do
    let c ← match ← clientRef.get with
      | some c => pure c
      | none => do
        let cfg : TypeSafe.Config := { maxRetries := 0, timeoutSeconds := 5 }
        let c ← (if usePass then TypeSafe.Client.fromPass (config := cfg)
          else TypeSafe.Client.fromEnv cfg).toIO (IO.userError ∘ toString)
        clientRef.set (some c)
        pure c
    jevRanker c state choices
  let stats ← IO.mkRef ({} : Stats)
  solve goals config (if live then some ranker else none) stats
  setGoals []
  if let [g] := goals then
    let winner := (← stats.get).winner
    if portfolioCodes.contains winner then
      let stx ← ofExcept <| Parser.runParserCategory (← getEnv) `tactic winner
      TryThis.addSuggestion (← getRef) { suggestion := (⟨stx⟩ : TSyntax `tactic) }
      return
    let proof ← inlineAuxiliaries original (← instantiateMVars (.mvar g))
    TryThis.addExactSuggestion (← getRef) proof (checkState? := initial) (tacticErrorAsInfo := true)

/-- Offline control for the Jev finishing architecture. -/
syntax (name := jevFinish2) "jev_finish2" optConfig : tactic
/-- Jev-guided premise selection and lookahead. Reads TYPESAFE_API_KEY on demand. -/
syntax (name := jevFinish2Live) "jev_finish2_live" optConfig : tactic
/-- Explicit live variant using the repository's pass credential entry. -/
syntax (name := jevFinish2Pass) "jev_finish2_pass" optConfig : tactic

elab_rules : tactic
  | `(tactic| jev_finish2 $cfg:optConfig) => do evalFinish false false (← elabAdvancedConfig cfg)
  | `(tactic| jev_finish2_live $cfg:optConfig) => do evalFinish true false (← elabAdvancedConfig cfg)
  | `(tactic| jev_finish2_pass $cfg:optConfig) => do evalFinish true true (← elabAdvancedConfig cfg)

end JevPilot.Advanced
