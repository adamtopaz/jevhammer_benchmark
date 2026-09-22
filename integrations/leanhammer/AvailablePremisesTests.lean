import AvailablePremises
import AvailableFixture

open Lean Meta Elab Command JevSelector
set_option maxHeartbeats 1000000

-- A current-file declaration must never enter the imported fit or postings,
-- even when its namespace resembles an imported declaration's namespace.
theorem AvailableFixture.current (n : Nat) : AvailableFixture.marker n := rfl

run_cmd liftTermElabM do
  let idx ← AvailablePremises.build #["AvailableFixture"] #[``AvailableFixture.heldout]
  unless idx.artifact.eligible == #["AvailableFixture.first", "AvailableFixture.later"] do
    throwError "wrong fitting rows: {idx.artifact.eligible}"
  unless idx.artifact.excluded == #["AvailableFixture.heldout", "AvailableFixture.heldout.child"] do
    throwError "owner/child exclusions were not applied"
  unless idx.artifact.candidateOnly == #["AvailableFixture.marker"] do
    throwError "definitions contributed to fitting"
  if idx.artifact.declarations.any (·.name == "AvailableFixture.current") then
    throwError "current-file declaration entered the imported catalog"
  unless idx.weights.getD "AvailableFixture.marker" 0 == 1 do
    throwError "IDF differs from eligible statement counts"
  discard <| idx.validateHoldouts #[``AvailableFixture.heldout]
  let rejected ← try
    discard <| idx.validateHoldouts #[``AvailableFixture.first]
    pure false
  catch _ => pure true
  unless rejected do throwError "overlapping training row was accepted"
  let goal ← mkFreshExprMVar (mkApp (mkConst ``AvailableFixture.marker) (mkNatLit 5))
  let result ← idx.targetSelector goal.mvarId! {
    maxSuggestions := 10
    filter := fun n => pure (n == ``AvailableFixture.current) }
  unless result.map (·.name) == #[``AvailableFixture.current] do
    throwError "earlier current-file premise was not supplied live"
  IO.println "AVAILABLE_PREMISES_TESTS_PASSED"
