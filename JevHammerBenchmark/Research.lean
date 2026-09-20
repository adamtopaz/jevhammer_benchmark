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

def closingTarget : Method := {
  target with
  selector := JevSelector.closingFirst target.selector
  selectorName := "JevSelector target + closing-first: pool=100, probes=64, heartbeats=1000, subgoals=4" }

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

initialize usageCache : IO.Ref (Option (String × JevSelector.UsageIndex)) ← IO.mkRef none

def usageIndex : IO JevSelector.UsageIndex := do
  let some path ← IO.getEnv "JEVSELECTOR_USAGE"
    | throw <| IO.userError "set JEVSELECTOR_USAGE to a prepared usage.json"
  if let some (previous, model) ← usageCache.get then
    unless previous == path do throw <| IO.userError "usage artifact path changed during a run"
    return model
  let model ← JevSelector.loadUsage (← Prepared.index) path
  unless model.artifact.smoothingMass == 20 && model.artifact.maxFeatures == 64 do
    throw <| IO.userError "usage-v1 requires smoothing mass 20 and top 64 corrections"
  usageCache.set (some (path, model))
  return model

def usage : Method := {
  Prepared.sparse with
  selector := fun goal cfg => do (← usageIndex).selector {} goal cfg
  selectorName := "JevSelector usage-v1: smoothing mass 20, top 64 feature corrections, full normalizer"
  warmup := do (← usageIndex).validateEnvironment
  validate := fun owners => do (← usageIndex).validateHoldouts owners }

initialize publicCache : IO.Ref (Option (String × JevSelector.Index)) ← IO.mkRef none

def publicIndex : IO JevSelector.Index := do
  let some path ← IO.getEnv "JEVSELECTOR_PUBLIC_INDEX"
    | throw <| IO.userError "set JEVSELECTOR_PUBLIC_INDEX to an expanded public catalog"
  if let some (previous, idx) ← publicCache.get then
    unless previous == path do throw <| IO.userError "public catalog path changed during a run"
    return idx
  let idx ← JevSelector.load path
  unless idx.artifact.publicConstants do
    throw <| IO.userError "public-catalog method requires publicConstants = true"
  publicCache.set (some (path, idx))
  return idx

def publicTarget : Method := {
  Prepared.sparse with
  selector := fun goal cfg => do (← publicIndex).targetSelector goal cfg
  selectorName := "JevSelector public-catalog target: definitions/constructors, theorem-only IDF"
  warmup := do (← publicIndex).validateEnvironment
  validate := fun owners => do (← publicIndex).validateHoldouts owners }

initialize publicDependencyCache : IO.Ref (Option (String × JevSelector.DependencyIndex)) ← IO.mkRef none

def publicDependencyIndex : IO JevSelector.DependencyIndex := do
  let some path ← IO.getEnv "JEVSELECTOR_PUBLIC_DEPENDENCIES"
    | throw <| IO.userError "set JEVSELECTOR_PUBLIC_DEPENDENCIES to a public-label model"
  if let some (previous, model) ← publicDependencyCache.get then
    unless previous == path do throw <| IO.userError "public-label path changed during a run"
    return model
  let model ← JevSelector.loadDependencies (← publicIndex) path
  unless model.artifact.publicLabels do
    throw <| IO.userError "public-label method requires publicLabels = true"
  publicDependencyCache.set (some (path, model))
  return model

def publicNeighbors : Method := {
  Prepared.sparse with
  selector := fun goal cfg => do (← publicDependencyIndex).selector {} goal cfg
  selectorName := "JevSelector public-label neighbors: 32 eligible theorem examples, direct public labels"
  warmup := do (← publicDependencyIndex).validateEnvironment
  validate := fun owners => do (← publicDependencyIndex).validateHoldouts owners }

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

def closingNeural : Method := {
  neuralWarm with
  selector := JevSelector.closingFirst neuralWarm.selector
  selectorName := "Warmed LeanPremise neural + closing-first: pool=100, probes=64, heartbeats=1000, subgoals=4" }

end JevHammerBenchmark.Research
