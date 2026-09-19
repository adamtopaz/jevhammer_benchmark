module
public meta import JevHammerBenchmark.Selector
public meta import JevHammerBenchmark.Neural
public meta section
namespace JevHammerBenchmark.Research
open Lean Meta LibrarySuggestions

def target : Method := {
  Prepared.sparse with
  selector := fun goal cfg => do (← Prepared.index).targetSelector goal cfg
  selectorName := "JevSelector target-v1: target=4, context=1, pivot=0.75" }

def ensemble : Method := {
  Prepared.sparse with
  selector := fun goal cfg => do (← Prepared.index).ensembleSelector {} goal cfg
  selectorName := "JevSelector fusion-v1: sparse+target, rankOffset=16, poolFactor=2, maxPool=256" }

initialize dependencyCache : IO.Ref (Option (String × JevSelector.DependencyIndex)) ← IO.mkRef none

def dependencyIndex : IO JevSelector.DependencyIndex := do
  let some path ← IO.getEnv "JEVSELECTOR_DEPENDENCIES"
    | throw <| IO.userError "set JEVSELECTOR_DEPENDENCIES to a prepared dependencies.json"
  if let some (previous, model) ← dependencyCache.get then
    unless previous == path do throw <| IO.userError "dependency artifact path changed during a run"
    return model
  let model ← JevSelector.loadDependencies (← Prepared.index) path
  dependencyCache.set (some (path, model))
  return model

def neighbors : Method := {
  Prepared.sparse with
  selector := fun goal cfg => do (← dependencyIndex).selector {} goal cfg
  selectorName := "JevSelector proof-neighbors-v1: 32 neighbors, reciprocal-rank votes, label IDF"
  warmup := do (← dependencyIndex).validateEnvironment
  validate := fun owners => do (← dependencyIndex).validateHoldouts owners }

def proofHybrid : Method := {
  neighbors with
  selector := fun goal cfg => do (← dependencyIndex).hybridSelector {} goal cfg
  selectorName := "JevSelector proof-hybrid-v1: sparse+proof-neighbors, rankOffset=16, poolFactor=2, maxPool=256" }

/-- Strong reference with both imported and earlier current-file statement
embeddings warmed outside the goal clock. The actual goal is embedded only
when the selector runs. Initialization cost is recorded by the harness. -/
def neuralWarm : Method := {
  Neural.neural with
  config := { guidePremises := false }
  selectorName := "LeanPremise neural service (imported and current-file catalog warmed)"
  warmup := do
    Neural.neural.warmup
    let some url ← IO.getEnv "JEVBENCH_NEURAL_URL"
      | throwError "set JEVBENCH_NEURAL_URL"
    withOptions (·.set `premiseSelection.apiBaseUrl url) do
      let modules ← Cloud.getIndexedImportedModules
      let premises ← Cloud.getUnindexedPremises
      discard <| Cloud.selectPremisesCore "⊢ True" #[] modules premises 1 }

end JevHammerBenchmark.Research
