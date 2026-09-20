import JevHammerBenchmark.RerankStudy
open Lean Elab Command JevHammerBenchmark RerankStudy
run_cmd do
  unless !cpuNative.config.guidePremises && cpuReranked.config.guidePremises &&
      !neuralNative.config.guidePremises && neuralReranked.config.guidePremises do
    throwError "reranking factors are not configured correctly"
  let expected := toJson ({ cpuNative.config with guidePremises := false } : JevHammer.Config)
  for method in #[cpuReranked, neuralNative, neuralReranked] do
    unless toJson ({ method.config with guidePremises := false } : JevHammer.Config) == expected do
      throwError "reranking changed another search configuration field"
    unless method.tacticSetName == cpuNative.tacticSetName do
      throwError "reranking comparison changed tactics"
