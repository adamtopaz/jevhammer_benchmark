import JevHammerBenchmark.GraphStudy
open Lean Meta Elab Command JevHammerBenchmark
set_option maxHeartbeats 4000000

run_cmd liftTermElabM do
  let guided := GraphStudy.guided
  let control := GraphStudy.cpuControl
  unless (methodInfo "guided" guided).getObjValD "selectorGuidance" == .bool true &&
      (methodInfo "control" control).getObjValD "selectorGuidance" == .bool false do
    throwError "method metadata does not expose selector guidance"
  unless toJson guided.config == toJson control.config &&
      guided.tacticSetName == control.tacticSetName &&
      guided.warmupHeartbeats == control.warmupHeartbeats do
    throwError "graph adapter changed the matched search configuration"
  -- No artifacts, initialization or credentials are required for a zero request.
  let goal ← mkFreshExprMVar (mkConst ``True)
  let rank : JevHammer.SelectorRanker := fun _ _ _ =>
    throwError "zero requested premises called Jev"
  -- Exercise the structural compatibility without the adapter's lazy cache:
  let graph ← JevSelector.DependencyGraph.create
  let compatible : JevHammer.SelectorFactory := graph.guided GraphStudy.graphOptions
  unless (← compatible rank LibrarySuggestions.empty goal.mvarId! { maxSuggestions := 0 }).isEmpty do
    throwError "graph ignored zero requested premises"
