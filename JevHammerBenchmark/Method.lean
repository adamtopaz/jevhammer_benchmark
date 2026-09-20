module

public meta import JevHammer

public meta section
namespace JevHammerBenchmark
open Lean Meta

deriving instance ToJson, FromJson for JevHammer.Config

/-- A reusable benchmark arm. Declare values of this type in any imported module
and select their fully qualified names in the driver; no runner changes needed. -/
structure Method where
  selector : LibrarySuggestions.Selector
  tactics : JevHammer.TacticSet := JevHammer.defaultTactics
  config : JevHammer.Config := {}
  /-- Human-readable identities supplement the compiled method's source hash. -/
  selectorName : String
  tacticSetName : String := "JevHammer.defaultTactics"
  /-- Goal-independent initialization. Its duration is reported separately. -/
  warmup : MetaM Unit := pure ()
  /-- Independent initialization budget, unaffected by the source tactic's
inherited MetaM heartbeat limit. Zero disables this limit; the runner's module
timeout and aggregate memory limit still apply. -/
  warmupHeartbeats : Nat := 5000000
  /-- Admission/provenance hook, receiving ALL evaluation owners in the run.
  Prepared selectors should reject overlap here before any trial executes. -/
  validate : Array Name → MetaM Json := fun _ => pure <|
    Json.mkObj [("training", .str "none")]

/-- Admit and initialize a method outside its proof-search budget, restoring
Lean state on both success and failure. IO caches intentionally survive. -/
def Method.runWarmup (method : Method) (owners : Array Name) : MetaM Json :=
  JevHammer.withHeartbeatBudget method.warmupHeartbeats do
    let saved ← saveState
    try
      let provenance ← method.validate owners
      method.warmup
      return provenance
    finally saved.restore

def methodInfo (name : String) (method : Method) : Json := Json.mkObj [
  ("name", toJson name), ("selector", toJson method.selectorName),
  ("tactics", toJson method.tacticSetName), ("config", toJson method.config),
  ("warmupHeartbeats", toJson method.warmupHeartbeats)]

def loadMethod (name : String) : MetaM Method := do
  unsafe evalConstCheck Method ``Method name.toName

end JevHammerBenchmark
