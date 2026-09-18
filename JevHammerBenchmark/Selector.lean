module
public meta import JevHammerBenchmark.Methods
public meta import JevSelector
public meta section
namespace JevHammerBenchmark.Prepared
open Lean Meta

initialize cache : IO.Ref (Option (String × JevSelector.Index)) ← IO.mkRef none

def index : IO JevSelector.Index := do
  let some path ← IO.getEnv "JEVSELECTOR_INDEX"
    | throw <| IO.userError "set JEVSELECTOR_INDEX to a prepared index.json"
  if let some (previous, idx) ← cache.get then
    unless previous == path do throw <| IO.userError "artifact path changed during a run"
    return idx
  let idx ← JevSelector.load path
  cache.set (some (path, idx))
  return idx

def sparse : Method := {
  selector := fun goal cfg => do (← index).selector {} goal cfg
  selectorName := "JevSelector statement-symbol-idf-v1"
  tactics := Methods.mathlibTactics
  tacticSetName := "JevHammerBenchmark.Methods.mathlibTactics"
  warmup := do (← index).validateEnvironment
  validate := fun owners => do (← index).validateHoldouts owners }

def sparseReranked : Method := {
  sparse with
  config := { guidePremises := true } }

end JevHammerBenchmark.Prepared
