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
