import JevHammerBenchmark.BayesStudy
open Lean Elab Command JevHammerBenchmark BayesStudy
run_cmd do
  for method in #[cpuControl, bayes, bayesTarget, bayesStructuralTarget] do
    if method.config.guidePremises then
      throwError "CPU Bayes comparison unexpectedly enabled premise reranking"
    unless toJson method.config == toJson cpuControl.config do
      throwError "CPU Bayes comparison changed a search configuration field"
  unless neuralControl.config.guidePremises do
    throwError "neural control omitted selected premise reranking"
  let expected := toJson ({ cpuControl.config with guidePremises := false } : JevHammer.Config)
  for method in #[bayes, bayesTarget, bayesStructuralTarget, neuralControl] do
    unless toJson ({ method.config with guidePremises := false } : JevHammer.Config) == expected do
      throwError "Bayes comparison changed another search configuration field"
    unless method.tacticSetName == cpuControl.tacticSetName do
      throwError "Bayes comparison changed tactics"
  let bounds : JevSelector.BayesQueryConfig := {}
  unless bounds.heartbeats == 10000 && bounds.maxPostingsPerSymbol == 20000 do
    throwError "Bayes defaults changed from the frozen protocol"
  let fusion : JevSelector.FusionConfig := {}
  unless fusion.rankOffset == 16 && fusion.poolFactor == 2 && fusion.maxPool == 256 do
    throwError "rank fusion defaults changed from the frozen protocol"
