import JevHammerBenchmark.Ranker

open Lean Elab Command JevHammerBenchmark JevHammer

run_cmd do
  for seed in [:40] do
    for size in [:40] do
      let (order, _) := randomOrder size (mkStdGen seed)
      unless isPermutation order size do throwError "random ranking repeated or omitted a choice"
      unless order == (randomOrder size (mkStdGen seed)).1 do
        throwError "random ranking is not reproducible"
  let directory := System.FilePath.mk s!".lake/ranking-policy-tests-{← IO.monoNanosNow}"
  IO.FS.createDirAll directory
  let usage := toJson ({} : UsageBudget)
  writeJsonAtomic (directory / "usage.json") usage
  let blocked ← IO.mkRef false
  let state := Json.mkObj [("task", .str "continuations")]
  let choices := (List.range 12).toArray.map toJson
  let fixed ← budgetedRanker directory "test-site" "fixed" {} 0 0 false blocked "fixed"
  let first ← budgetedRanker directory "test-site" "a" {} 0 0 false blocked "random" 17
  let second ← budgetedRanker directory "test-site" "b" {} 0 0 false blocked "random" 17
  let other ← budgetedRanker directory "test-site" "c" {} 0 0 false blocked "random" 18
  let mut differs := false
  let mut changes := false
  let mut previous := #[]
  for _ in [:4] do
    unless (← fixed state choices).order == (List.range 12).toArray do
      throwError "fixed ranking changed candidate order"
    let a ← first state choices
    unless a.order == (← second state choices).order do
      throwError "identical per-site seed changed stream across methods"
    differs := differs || a.order != (← other state choices).order
    changes := changes || (!previous.isEmpty && previous != a.order)
    previous := a.order
    unless a.model == "LOCAL-RANDOM" do throwError "baseline mislabeled as model guidance"
  unless differs && changes do throwError "seed or persistent random stream has no effect"
  unless (← IO.ofExcept <| Json.parse (← IO.FS.readFile (directory / "usage.json"))) == usage do
    throwError "local ranking touched API usage"
  if ← blocked.get then throwError "local ranking consumed request budget"
  for (policy, mock) in [("invalid", false), ("random", true)] do
    let rejected ← try
      discard <| budgetedRanker directory "s" "m" {} 0 0 mock blocked policy
      pure false
    catch _ => pure true
    unless rejected do throwError "invalid ranking configuration accepted"
  IO.println "RANKING_POLICY_TESTS_PASSED"
