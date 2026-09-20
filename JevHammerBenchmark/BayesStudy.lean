module
public meta import JevHammerBenchmark.RerankStudy
public meta import JevSelector.Bayes
public meta section
namespace JevHammerBenchmark.BayesStudy
open Lean Meta LibrarySuggestions

initialize bayesCache : IO.Ref (Option (String × JevSelector.BayesIndex)) ← IO.mkRef none

def bayesIndex : IO JevSelector.BayesIndex := do
  let some path ← IO.getEnv "JEVSELECTOR_BAYES"
    | throw <| IO.userError "set JEVSELECTOR_BAYES to the held-out sparse Bayes artifact"
  if let some (previous, model) ← bayesCache.get then
    unless previous == path do throw <| IO.userError "Bayes artifact path changed during a run"
    return model
  let model ← JevSelector.loadBayes (← Research.publicIndex) path
  unless model.header.signaturePrior == 20 && model.header.observedWeight == 10 &&
      model.header.missingWeight == -15 && model.header.maxFeatures == 64 do
    throw <| IO.userError "Bayes study requires the frozen 20/10/-15/top64 recipe"
  bayesCache.set (some (path, model))
  return model

def bayesSelector : Selector := fun goal cfg => do
  (← bayesIndex).selector {} goal cfg

def cpuControl : Method := RerankStudy.cpuNative

def neuralControl : Method := RerankStudy.neuralReranked

def bayes : Method := {
  cpuControl with
  selector := bayesSelector
  selectorName := "Sparse Bayes: eligible signature prior 20, observed 10, missing -15, top64"
  warmup := do
    (← bayesIndex).validateEnvironment
  validate := fun owners => do (← bayesIndex).validateHoldouts owners }

def bayesTarget : Method := {
  bayes with
  selector := JevSelector.fuse #[Research.publicTarget.selector, bayesSelector] {}
  selectorName := "Public sparse + weighted Bayes, native premise order"
  warmup := do
    Research.publicTarget.warmup
    bayes.warmup
  validate := fun owners => do
    return Json.mkObj [("sparse", ← Research.publicTarget.validate owners),
      ("bayes", ← bayes.validate owners)] }

def bayesStructuralTarget : Method := {
  bayesTarget with
  selector := JevSelector.fuse #[Research.publicTarget.selector,
    Research.structuralSelector "bayes-structural-target", bayesSelector] {}
  selectorName := "Public sparse + conclusion patterns + weighted Bayes, native premise order"
  warmup := do
    bayesTarget.warmup
    discard <| Research.structuralIndex "bayes-structural-target"
  validate := fun owners => do
    return Json.mkObj [("learned", ← bayesTarget.validate owners),
      ("conclusions", ← Research.structuralProvenance owners)] }

end JevHammerBenchmark.BayesStudy
