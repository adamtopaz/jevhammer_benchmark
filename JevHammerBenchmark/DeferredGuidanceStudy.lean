module
public meta import JevHammerBenchmark.GraphPreviewStudy
public meta section
namespace JevHammerBenchmark.DeferredGuidanceStudy
open Lean Meta

/-- Give every selector the same opportunity to finish before spending model
calls on premise guidance. Unguided methods retain their original path. -/
def deferred (method : Method) : Method := {
  method with
  config := { method.config with deferPremiseGuidance := true }
  selectorName := method.selectorName ++ "; timed base-premise finish before guidance"
  validate := fun owners => do
    return (← method.validate owners).mergeObj <| Json.mkObj [
      ("guidanceSchedule", toJson "base finish, then guidance if needed; same clock and calls")] }

-- These existing adapters already use separate mutable structural caches.
def cpuControl : Method := deferred RerankStudy.cpuNative
def cpuReranked : Method := deferred RerankStudy.cpuReranked
def graphPreview : Method := deferred GraphPreviewStudy.preview
def neuralNative : Method := deferred RerankStudy.neuralNative
def neuralReranked : Method := deferred RerankStudy.neuralReranked

end JevHammerBenchmark.DeferredGuidanceStudy
