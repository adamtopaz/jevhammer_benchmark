import JevHammerBenchmark.Method
open Lean Meta Elab Command JevHammerBenchmark

run_cmd liftTermElabM do
  let _ : MonadExceptOf Exception MetaM :=
    { (inferInstance : MonadExceptOf Exception MetaM) with tryCatch := tryCatchRuntimeEx }
  let goal ← mkFreshExprMVar (mkConst ``True)
  let validated ← IO.mkRef false
  let method : Method := {
    selector := LibrarySuggestions.empty
    selectorName := "warmup budget fixture"
    warmupHeartbeats := 20
    validate := fun owners => do
      unless owners == #[`Fixture.owner] do throwError "lost evaluation owners"
      IO.addHeartbeats 5000
      Core.checkMaxHeartbeats "warmup-validation"
      validated.set true
      pure <| Json.mkObj [("fixture", .bool true)]
    warmup := do
      IO.addHeartbeats 5000
      Core.checkMaxHeartbeats "warmup-initialization"
      goal.mvarId!.assign (mkConst ``True.intro) }
  -- Reproduce the previous inherited-budget behavior without costly work.
  let oldFailed ← try
    JevHammer.withHeartbeatBudget 1 do
      discard <| method.validate #[`Fixture.owner]
      method.warmup
    pure false
  catch _ => pure true
  unless oldFailed do throwError "legacy warmup did not exhaust the inherited budget"
  let provenance ← JevHammer.withHeartbeatBudget 1 <| method.runWarmup #[`Fixture.owner]
  unless provenance.getObjValD "fixture" == .bool true && (← validated.get) do
    throwError "independent warmup failed to run admission"
  if ← goal.mvarId!.isAssigned then throwError "successful warmup leaked Lean state"
  let rejected ← try
    discard <| { method with warmupHeartbeats := 1 }.runWarmup #[`Fixture.owner]
    pure false
  catch _ => pure true
  unless rejected do throwError "warmup ignored its own finite heartbeat limit"
  let throwing : Method := { method with warmup := do
    goal.mvarId!.assign (mkConst ``True.intro)
    throwError "fixture failure" }
  let failed ← try
    discard <| throwing.runWarmup #[`Fixture.owner]
    pure false
  catch _ => pure true
  unless failed do throwError "warmup swallowed a failure"
  if ← goal.mvarId!.isAssigned then throwError "failed warmup leaked Lean state"
