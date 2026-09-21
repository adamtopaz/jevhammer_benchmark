import LeanHammerComparison
set_option maxHeartbeats 1000000
set_option Elab.async false
set_option hammer.singleTacticParallel true

-- Each engine is exercised independently, through upstream's parallel proof
-- packaging. Only these offline backend tests disable competing engines.
example (p q : Prop) (h : p) (f : p → q) : q := by
  hammer {parallelism := false, disableDuper := true, disableGrind := true,
    disableSmt := true, aesopPremises := 0}
example (p q : Prop) (h : p) (f : p → q) : q := by
  hammer {parallelism := false, disableAesop := true, disableGrind := true,
    disableSmt := true, preprocessing := no_preprocessing,
    duperPremisesShort := 0, duperPremisesLong := 0}
example (p q : Prop) (h : p) (f : p → q) : q := by
  hammer {parallelism := false, disableAesop := true, disableDuper := true,
    disableSmt := true, preprocessing := no_preprocessing, grindPremises := 0}
example (a b : Int) (h₁ : a + 1 ≤ b) (h₂ : b ≤ a) : False := by
  hammer {parallelism := false, disableAesop := true, disableDuper := true,
    disableGrind := true, preprocessing := no_preprocessing, smtPremises := 0}
example (p q : Prop) (h : p) (f : p → q) : q := by
  hammer {aesopPremises := 0, duperPremisesShort := 0, duperPremisesLong := 0,
    grindPremises := 0, smtPremises := 0}

open Lean Meta Elab Command JevHammerBenchmark in
run_cmd liftTermElabM do
  unless toJson LeanHammerComparison.cpu.config == toJson LeanHammerComparison.neural.config &&
      LeanHammerComparison.cpu.tacticSetName == LeanHammerComparison.neural.tacticSetName do
    throwError "JevHammer controls do not match"
  let full := LeanHammerComparison.full
  unless full.config.maxCalls == 0 && full.config.maxNodes == 0 &&
      full.config.tacticHeartbeats == 200000 do
    throwError "full LeanHammer acquired an extra search or a per-step handicap"
