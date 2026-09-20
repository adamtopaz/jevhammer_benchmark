import JevHammerBenchmark.GraphPreviewStudy
open Lean Meta Elab Command JevHammerBenchmark
set_option maxHeartbeats 4000000

run_cmd liftTermElabM do
  let control := GraphPreviewStudy.cpuControl
  for method in #[GraphPreviewStudy.original, GraphPreviewStudy.preview,
      GraphPreviewStudy.neuralNative, GraphPreviewStudy.neuralReranked] do
    unless toJson { method.config with guidePremises := false } == toJson control.config &&
        method.tacticSetName == control.tacticSetName &&
        method.warmupHeartbeats == control.warmupHeartbeats do
      throwError "preview study changed matched search settings"
  for method in #[control, GraphPreviewStudy.original, GraphPreviewStudy.preview,
      GraphPreviewStudy.neuralNative] do
    if method.config.guidePremises then throwError "native-order method reranks premises"
  unless GraphPreviewStudy.neuralReranked.config.guidePremises do
    throwError "neural reranking was disabled"
  for method in #[GraphPreviewStudy.original, GraphPreviewStudy.preview] do
    unless method.selectorFactory.isSome do throwError "graph method lost selector guidance"
  for method in #[control, GraphPreviewStudy.neuralNative, GraphPreviewStudy.neuralReranked] do
    if method.selectorFactory.isSome then throwError "control acquired graph guidance"
  unless GraphStudy.graphOptions.maxPreviewCandidates == 0 &&
      GraphPreviewStudy.previewOptions.maxPreviewCandidates == 3 &&
      GraphPreviewStudy.previewOptions.maxPreviewTypeChars == 480 do
    throwError "graph preview representation is not the frozen ablation"
  let graph ← JevSelector.DependencyGraph.create
  let compatible : JevHammer.SelectorFactory := graph.guided GraphPreviewStudy.previewOptions
  let goal ← mkFreshExprMVar (mkConst ``True)
  let rank : JevHammer.SelectorRanker := fun _ _ _ => throwError "zero request called Jev"
  unless (← compatible rank LibrarySuggestions.empty goal.mvarId! { maxSuggestions := 0 }).isEmpty do
    throwError "preview adapter ignored zero suggestions"
