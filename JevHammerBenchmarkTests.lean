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
