import JevHammerBenchmark.BayesExactStudy
open Lean Elab Command JevHammerBenchmark BayesExactStudy
run_cmd do
  let expected := toJson cpuControl.config
  for method in #[sampled, exhaustive, sampledTarget, exhaustiveTarget] do
    unless toJson method.config == expected && !method.config.guidePremises do
      throwError "Bayes posting comparison changed a CPU search setting"
    unless method.tacticSetName == cpuControl.tacticSetName &&
        method.warmupHeartbeats == cpuControl.warmupHeartbeats do
      throwError "Bayes posting comparison changed tactics or initialization limits"
  unless neuralControl.config.guidePremises &&
      toJson ({ neuralControl.config with guidePremises := false } : JevHammer.Config) == expected do
    throwError "neural control changed from the selected premise guidance policy"
  unless cpuControl.config.maxMillis == 6000 && cpuControl.config.maxCalls == 3 do
    throwError "proof budget changed"
  let sampledOptions : JevSelector.BayesQueryConfig := {}
  unless sampledOptions.maxPostingsPerSymbol == 20000 &&
      exhaustiveOptions.maxPostingsPerSymbol == 0 &&
      sampledOptions.heartbeats == exhaustiveOptions.heartbeats &&
      exhaustiveOptions.heartbeats == 10000 do
    throwError "query cap ablation changed another retrieval bound"
  let fusion : JevSelector.FusionConfig := {}
  unless fusion.rankOffset == 16 && fusion.poolFactor == 2 && fusion.maxPool == 256 do
    throwError "rank fusion defaults changed"
