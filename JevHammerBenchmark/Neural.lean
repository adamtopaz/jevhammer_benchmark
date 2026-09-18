module
public meta import JevHammerBenchmark.Methods
public meta import PremiseSelection.Cloud
public meta section
namespace JevHammerBenchmark.Neural
open Lean Meta LibrarySuggestions

private def configured (action : MetaM α) : MetaM α := do
  let some url ← IO.getEnv "JEVBENCH_NEURAL_URL"
    | throwError "set JEVBENCH_NEURAL_URL to an explicitly chosen premise service"
  let mut env ← getEnv
  for mod in #["Hammer", "Smt", "Duper", "Auto", "Aesop", "cvc5"] do
    env := moduleDenyListExt.addEntry env mod
  withEnv env <| withOptions (·.set `premiseSelection.apiBaseUrl url) action

/-- Neural premise selection with Jev premise reranking and Jev state guidance.
The service/model provenance is supplied by the operator; no default endpoint
or claim of proof-disjoint third-party training is assumed. -/
def neural : Method := {
  selector := fun goal cfg => configured do
    let suggestions ← Cloud.premiseSelector goal { cfg with caller := "hammer" }
    let env ← getEnv
    suggestions.filterM fun s => do
      return env.contains s.name && (← cfg.filter s.name)
  selectorName := "LeanPremise neural service"
  tactics := Methods.mathlibTactics
  tacticSetName := "JevHammerBenchmark.Methods.mathlibTactics"
  config := { guidePremises := true }
  warmup := configured do
    let modules ← Cloud.getIndexedImportedModules
    let unindexed ← Cloud.getUnindexedImportedPremises
    discard <| Cloud.selectPremisesCore "⊢ True" #[] modules unindexed 1
  validate := fun _ => do
    let some path ← IO.getEnv "JEVBENCH_NEURAL_PROVENANCE"
      | throwError "set JEVBENCH_NEURAL_PROVENANCE to model/corpus/deployment metadata JSON"
    let metadata ← IO.ofExcept (Json.parse (← IO.FS.readFile path))
    for field in ["model", "corpus", "serverRevision", "trainingOverlap"] do
      unless (metadata.getObjVal? field).isOk do throwError "missing provenance field {field}"
    return metadata }

end JevHammerBenchmark.Neural
