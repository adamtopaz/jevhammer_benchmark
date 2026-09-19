import JevHammerBenchmark

open Lean Meta Elab Command JevHammerBenchmark

run_cmd liftTermElabM do
  let proof := mkConst ``True.intro
  let cert := Certificate.encode proof (mkConst ``True)
  Certificate.verify cert (mkConst ``True)
  let failed ← try
    Certificate.verify cert (mkConst ``False)
    pure false
  catch _ => pure true
  unless failed do throwError "certificate accepted the wrong source target"
  let failed ← try
    Certificate.verify (Certificate.encode (← mkSorry (mkConst ``False) true) (mkConst ``False))
      (mkConst ``False)
    pure false
  catch _ => pure true
  unless failed do throwError "certificate accepted an admission"

example (p : Prop) (h : p) : p := by jev_hammer

run_cmd liftTermElabM do
  let proof := mkConst ``True.intro
  let rejected ← try
    Certificate.verify (Certificate.encode proof (mkConst ``True)) (mkConst ``True) "True.intro"
    pure false
  catch _ => pure true
  unless rejected do throwError "excluded owner appeared in certificate"


-- Individually valid certificates must still agree on a shared witness.
run_cmd liftTermElabM do
  let witness ← mkFreshExprMVar (mkConst ``Nat)
  let equality ← mkFreshExprMVar (← mkEq witness (mkNatLit 0))
  Certificate.assign (Certificate.encode (mkNatLit 1) (mkConst ``Nat)) witness.mvarId!
  let refl ← mkEqRefl (mkNatLit 0)
  let rejected ← try
    Certificate.assign (Certificate.encode refl (← inferType refl)) equality.mvarId!
    pure false
  catch _ => pure true
  unless rejected do throwError "inconsistent witness certificates were accepted"
  let witness ← mkFreshExprMVar (mkConst ``Nat)
  let equality ← mkFreshExprMVar (← mkEq witness (mkNatLit 0))
  Certificate.assign (Certificate.encode (mkNatLit 0) (mkConst ``Nat)) witness.mvarId!
  Certificate.assign (Certificate.encode refl (← inferType refl)) equality.mvarId!
  unless (← equality.mvarId!.isAssigned) do throwError "shared-goal replay did not assign the goal"
