import JevHammerBenchmark.RewriteStudy
open Lean Elab Command JevHammerBenchmark RewriteStudy
run_cmd do
  for method in #[cpuControl, cpuRewrites, signatureOnly] do
    if method.config.guidePremises then
      throwError "CPU rewrite comparison unexpectedly enabled premise reranking"
    unless toJson method.config == toJson cpuControl.config do
      throwError "CPU rewrite comparison changed a search configuration field"
  for method in #[neuralControl, neuralRewrites] do
    unless method.config.guidePremises do
      throwError "neural rewrite comparison omitted selected premise reranking"
    unless toJson method.config == toJson neuralControl.config do
      throwError "neural rewrite comparison changed a search configuration field"
  let expected := toJson ({ cpuControl.config with guidePremises := false } : JevHammer.Config)
  for method in #[cpuRewrites, signatureOnly, neuralControl, neuralRewrites] do
    unless toJson ({ method.config with guidePremises := false } : JevHammer.Config) == expected do
      throwError "rewrite comparison changed another search configuration field"
    unless method.tacticSetName == cpuControl.tacticSetName do
      throwError "rewrite comparison changed tactics"
  let bounds : JevSelector.StructuralConfig := {}
  unless bounds.heartbeats == 10000 && bounds.maxNodes == 256 &&
      bounds.maxQueries == 64 && bounds.maxDepth == 8 && bounds.maxHypotheses == 8 do
    throwError "rewrite defaults changed from the frozen protocol"
  let fusion : JevSelector.FusionConfig := {}
  unless fusion.rankOffset == 16 && fusion.poolFactor == 2 && fusion.maxPool == 256 do
    throwError "rank fusion defaults changed from the frozen protocol"
