import AvailablePremises
import Mathlib

open Lean Meta Elab Command JevSelector
set_option maxHeartbeats 5000000

-- Cross-check the in-memory fitter against the existing independently prepared
-- Python/Lean artifact when both are given exactly the same imported library.
-- This does not supply the full-library artifact to the strict benchmark arm.
run_cmd liftTermElabM do
  let some holdoutsPath ← IO.getEnv "JEVSELECTOR_HOLDOUTS"
    | throwError "set JEVSELECTOR_HOLDOUTS"
  let some indexPath ← IO.getEnv "JEVSELECTOR_PUBLIC_INDEX"
    | throwError "set JEVSELECTOR_PUBLIC_INDEX"
  let holdouts ← IO.ofExcept (Json.parse (← IO.FS.readFile holdoutsPath))
  let names : Array String ← ofExcept <| fromJson? (holdouts.getObjValD "declarations")
  let start ← IO.monoMsNow
  let fresh ← AvailablePremises.build #["Mathlib"] (names.map String.toName)
  let millis := (← IO.monoMsNow) - start
  let old ← JevSelector.load indexPath
  unless fresh.artifact.eligible == old.artifact.eligible &&
      fresh.artifact.candidateOnly == old.artifact.candidateOnly do
    throwError "fitting eligibility differs from the reference artifact"
  unless fresh.artifact.declarations.size == old.artifact.declarations.size do
    throwError "catalog size differs from the reference artifact"
  for (a, b) in fresh.artifact.declarations.zip old.artifact.declarations do
    unless a.name == b.name && a.symbols == b.symbols && a.typeHash == b.typeHash do
      throwError "catalog statement differs from the reference artifact"
  unless fresh.weights.size == old.weights.size && fresh.meanSymbolCount == old.meanSymbolCount do
    throwError "fitted statistics differ from reference"
  for (symbol, weight) in fresh.weights do
    unless Float.abs (weight - old.weights.getD symbol 0) < 0.000000000001 do
      throwError "symbol weight differs from the reference artifact"
  for (symbol, indices) in fresh.postings do
    unless old.postings.getD symbol #[] == indices do
      throwError "posting order differs from reference"
  IO.println s!"AVAILABLE_PREMISES_REFERENCE_MATCH:{millis}:{fresh.artifact.declarations.size}"
