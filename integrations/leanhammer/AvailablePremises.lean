module

public meta import JevSelector.Ensemble

public meta section
namespace AvailablePremises
open Lean Meta LibrarySuggestions JevSelector

/-- Build the sparse model solely from imported signatures in the current
environment. Current-file declarations are retrieved from their live types by
Index.selector, but never contribute to this imports-only fit. No full-library
artifact, proof body, or future/current-file signature is read during fitting. -/
def build (scopes : Array String) (holdouts : Array Name) : MetaM Index := do
  let env ← getEnv
  let excluded := fun name => holdouts.any (·.isPrefixOf name)
  let mut entries : Array Entry := #[]
  let mut eligible : Array String := #[]
  let mut candidates : Array String := #[]
  let mut heldout : Array String := #[]
  let mut df : Std.HashMap String Nat := {}
  let mut totalSymbols := 0
  for (name, info) in env.constants.map₁ do
    let mod := (moduleName env name).toString
    unless scopes.any (matchesScope mod) do continue
    if isDeniedSignature env name info.type then continue
    let e := entry env info
    entries := entries.push e
    if excluded name then
      heldout := heldout.push e.name
    else if wasOriginallyTheorem env name then
      eligible := eligible.push e.name
      totalSymbols := totalSymbols + e.symbols.size
      for symbol in e.symbols do
        df := df.insert symbol (df.getD symbol 0 + 1)
    else
      candidates := candidates.push e.name
  entries := entries.qsort (fun a b => a.name < b.name)
  eligible := eligible.qsort (· < ·)
  candidates := candidates.qsort (· < ·)
  heldout := heldout.qsort (· < ·)
  let weights := df.toArray.map fun (symbol, count) =>
    ({ symbol, weight := 1 + Float.log ((eligible.size + 1).toFloat / (count + 1).toFloat) } : Weight)
  let weights := weights.qsort (fun a b => a.symbol < b.symbol)
  let provenance := Json.mkObj [
    ("kind", toJson "available-imported-statements-v1"),
    ("fittingScope", toJson "imported signatures only; no current-file training rows"),
    ("proofInformation", toJson "none"), ("scopes", toJson scopes),
    ("importedModules", toJson (env.header.moduleNames.map Name.toString)),
    ("declarations", toJson entries.size), ("eligible", toJson eligible.size),
    ("candidateOnly", toJson candidates.size), ("excludedAvailable", toJson heldout.size),
    ("holdoutOwners", toJson holdouts.size), ("symbols", toJson weights.size),
    ("catalogHash", toJson (hash (entries.map fun e => (e.name, e.typeHash))).toNat),
    ("eligibleHash", toJson (hash eligible).toNat)]
  let artifact : Artifact := {
    schema := 1
    leanVersion := Lean.versionString
    declarations := entries
    weights := weights
    eligible := eligible
    excluded := heldout
    provenance := provenance
    publicConstants := true
    candidateOnly := candidates }
  let mut lists : Std.HashMap String (List Nat) := {}
  for (e, i) in entries.zipIdx do
    for symbol in e.symbols do lists := lists.insert symbol (i :: lists.getD symbol [])
  let mut postings := {}
  for (symbol, indices) in lists do postings := postings.insert symbol indices.reverse.toArray
  let mut trainingOwners : Std.HashSet String := {}
  for name in eligible do
    let mut ownerPrefix := ""
    for part in name.splitOn "." do
      ownerPrefix := if ownerPrefix.isEmpty then part else ownerPrefix ++ "." ++ part
      trainingOwners := trainingOwners.insert ownerPrefix
  return {
    artifact := artifact
    postings := postings
    weights := .ofArray (weights.map fun w => (w.symbol, w.weight))
    trainingOwners := trainingOwners
    eligibleNames := .ofArray eligible
    meanSymbolCount := max 1 (totalSymbols.toFloat / (max 1 eligible.size).toFloat) }

initialize cache : IO.Ref (Option Index) ← IO.mkRef none

def index : IO Index := do
  let some idx ← cache.get | throw <| IO.userError "available-premise model has not been initialized"
  return idx

def initializeModel (owners : Array Name) : MetaM Json := do
  let some path ← IO.getEnv "JEVSELECTOR_HOLDOUTS"
    | throwError "set JEVSELECTOR_HOLDOUTS to the complete study holdout file"
  let value ← IO.ofExcept (Json.parse (← IO.FS.readFile path))
  let names : Array String ← ofExcept <| fromJson? (value.getObjValD "declarations")
  let excludedModules : Array String ← ofExcept <| fromJson? (value.getObjValD "modules")
  unless excludedModules.isEmpty do throwError "this study requires declaration holdouts only"
  unless owners.all (fun n => names.contains n.toString) do
    throwError "study holdouts omit evaluation owners"
  let idx ← build #["Mathlib"] (names.map String.toName)
  discard <| idx.validateHoldouts (names.map String.toName)
  idx.validateEnvironment
  cache.set (some idx)
  return idx.artifact.provenance

end AvailablePremises
