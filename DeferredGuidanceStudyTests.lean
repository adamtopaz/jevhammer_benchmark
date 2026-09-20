import JevHammerBenchmark.DeferredGuidanceStudy
open Lean Meta Elab Command JevHammerBenchmark
set_option maxHeartbeats 4000000

run_cmd liftTermElabM do
  let methods := #[DeferredGuidanceStudy.cpuControl, DeferredGuidanceStudy.cpuReranked,
    DeferredGuidanceStudy.graphPreview, DeferredGuidanceStudy.neuralNative,
    DeferredGuidanceStudy.neuralReranked]
  let original := #[RerankStudy.cpuNative, RerankStudy.cpuReranked,
    GraphPreviewStudy.preview, RerankStudy.neuralNative, RerankStudy.neuralReranked]
  for (method, previous) in methods.zip original do
    unless method.config.deferPremiseGuidance &&
        toJson { method.config with deferPremiseGuidance := false } == toJson previous.config &&
        toJson { method.config with guidePremises := false } ==
          toJson DeferredGuidanceStudy.cpuControl.config &&
        method.tacticSetName == previous.tacticSetName &&
        method.warmupHeartbeats == previous.warmupHeartbeats &&
        method.selectorFactory.isSome == previous.selectorFactory.isSome &&
        method.config.guidePremises == previous.config.guidePremises do
      throwError "deferred study changed an unmatched setting or weakened a control"

  let encoded := (toJson ({} : JevHammer.Config)).mergeObj <|
    Json.mkObj [("deferPremiseGuidance", toJson true)]
  let config ← ofExcept <| fromJson? encoded (α := JevHammer.Config)
  unless config.deferPremiseGuidance && config.maxMillis == 6000 do
    throwError "public JSON override did not preserve configuration defaults"
