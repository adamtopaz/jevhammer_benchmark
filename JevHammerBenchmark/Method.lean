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
  /-- Admission/provenance hook, receiving ALL evaluation owners in the run.
  Prepared selectors should reject overlap here before any trial executes. -/
  validate : Array Name → MetaM Json := fun _ => pure <|
    Json.mkObj [("training", .str "none")]

def methodInfo (name : String) (method : Method) : Json := Json.mkObj [
  ("name", toJson name), ("selector", toJson method.selectorName),
  ("tactics", toJson method.tacticSetName), ("config", toJson method.config)]

def loadMethod (name : String) : MetaM Method := do
  unsafe evalConstCheck Method ``Method name.toName

end JevHammerBenchmark
