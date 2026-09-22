module
public meta import Hammer
public meta import JevHammerBenchmark.Research
public meta import JevHammerBenchmark.Ranker
public meta import AvailablePremises
public meta section
namespace LeanHammerComparison
open Lean Meta Elab Tactic LibrarySuggestions JevHammerBenchmark

structure SelectorStats where
  calls : Nat := 0
  elapsedMs : Nat := 0
  candidates : Nat := 0
  unavailable : Nat := 0
  fallbacks : Nat := 0
  errors : Array String := #[]
  deriving Inhabited, ToJson

initialize selectorStats : IO.Ref SelectorStats ← IO.mkRef {}

private def trackedCloud : Selector := fun goal cfg => do
  try Cloud.premiseSelector goal cfg
  catch e =>
    let message ← e.toMessageData.toString
    selectorStats.modify fun s => { s with
      fallbacks := s.fallbacks + 1, errors := s.errors.push message }
    throw e

/-- Preserve the pinned upstream cloud-or-Sine fallback. Only availability is
checked here; no Jev reranking or CPU fusion is added to the comparator. -/
def fullSelector : Selector := fun goal cfg => do
  let start ← IO.monoMsNow
  selectorStats.modify fun s => { s with calls := s.calls + 1 }
  try
    let suggestions ← (trackedCloud <|> sineQuaNonSelector.intersperse currentFile) goal cfg
    let env ← getEnv
    let available := suggestions.filter fun s => env.contains s.name
    selectorStats.modify fun s => { s with
      candidates := s.candidates + available.size
      unavailable := s.unavailable + suggestions.size - available.size }
    return available
  finally
    let elapsed := (← IO.monoMsNow) - start
    selectorStats.modify fun s => { s with elapsedMs := s.elapsedMs + elapsed }

private def record (status : String) : IO Unit := do
  let some path ← IO.getEnv "JEVHAMMER_BENCH_CONFIG" | return
  let settings ← IO.ofExcept <| Json.parse (← IO.FS.readFile path)
  unless settings.getObjValD "phase" == .str "run" do return
  let directory ← IO.ofExcept <| settings.getObjValAs? String "outputDir"
  appendJson (System.FilePath.mk directory / "leanhammer-selector.jsonl") <|
    (toJson (← selectorStats.get)).mergeObj (Json.mkObj [
      ("module", settings.getObjValD "moduleName"), ("status", toJson status)])

/-- A single unmodified full hammer invocation. Scoped registration prevents
source-file imports/registrations from silently replacing its neural selector. -/
elab "jevbench_full_leanhammer" : tactic => do
  let some url ← IO.getEnv "JEVBENCH_NEURAL_URL"
    | throwError "set JEVBENCH_NEURAL_URL for full LeanHammer"
  selectorStats.set {}
  let env := librarySuggestionsExt.addEntry (← getEnv) ``fullSelector
  try
    withEnv env <| withOptions (·.set `premiseSelection.apiBaseUrl url) do
      evalTactic (← `(tactic| hammer))
    record "solved"
  catch e =>
    record "failed"
    throw e

def cpu : Method := Research.structuralPublic
def neural : Method := Research.structuralNeural

/-- Same search and fusion as cpu; the sparse fit sees only currently imported
Mathlib statements. Earlier current-file candidates are supplied live at query
time and cannot alter fitted statistics or imported postings. -/
def strict : Method := {
  cpu with
  selector := JevSelector.fuse #[
    (fun goal cfg => do (← AvailablePremises.index).targetSelector goal cfg),
    Research.structuralSelector "available-imports-fusion"] {}
  selectorName := "Available imported statements only: target IDF + conclusion, live current-file candidates"
  warmup := do discard <| Research.structuralIndex "available-imports-fusion"
  validate := AvailablePremises.initializeModel }

/-- JevHammer dispatches exactly one closing tactic to reuse the harness's
atomicity/certificate gates. It performs no Jev search or premise retrieval. -/
def full : Method := {
  selector := LibrarySuggestions.empty
  selectorName := "Full LeanHammer: upstream neural with ordinary Sine fallback"
  tactics := { close := .fixed #["jevbench_full_leanhammer"] }
  tacticSetName := "Full LeanHammer 21886b7; all engines, default parallelism"
  config := { maxMillis := 6000, maxCalls := 0, maxNodes := 0, tacticHeartbeats := 200000 }
  warmup := Research.neuralWarm.warmup
  validate := fun owners => do
    return Json.mkObj [("neural", ← Research.neuralWarm.validate owners),
      ("upstreamRevision", toJson "21886b7ffbdf32017655a9d6e699f98779046533"),
      ("engines", toJson #["Aesop", "grind", "Lean-auto/Zipperposition/Duper", "Lean-SMT/cvc5"]),
      ("solverWallSeconds", toJson (5 : Nat)),
      ("endToEndDeadlineMs", toJson (6000 : Nat)),
      ("parallelism", toJson true), ("additionalJevSearch", toJson false)] }

end LeanHammerComparison
