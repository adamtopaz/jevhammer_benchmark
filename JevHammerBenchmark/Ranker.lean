module

public meta import JevHammerBenchmark.Method

public meta section
namespace JevHammerBenchmark
open Lean JevHammer JevPilot

structure UsageBudget where
  attempts : Nat := 0
  inputTokens : Nat := 0
  outputTokens : Nat := 0
  unknownUsage : Nat := 0
  deriving FromJson, ToJson

def writeJsonAtomic (path : System.FilePath) (json : Json) : IO Unit := do
  let temp := System.FilePath.mk (path.toString ++ ".tmp")
  IO.FS.writeFile temp (json.compress ++ "\n")
  IO.FS.rename temp path

def appendJson (path : System.FilePath) (json : Json) : IO Unit := do
  let handle ← IO.FS.Handle.mk path .append
  handle.putStrLn json.compress
  handle.flush

/-- The driver serializes all processes in a run. Reserve requests on disk before
network IO so failed calls and interrupted runs retain their accounting. -/
private def jevRanker (directory : System.FilePath) (site method : String)
    (config : JevHammer.Config) (maxRequests maxInputTokens : Nat)
    (mock : Bool) (blocked : IO.Ref Bool) : IO Ranker := do
  if mock then return fun _ choices => pure {
    order := (List.range choices.size).toArray, model := "OFFLINE-MOCK" }
  let client ← IO.mkRef (none : Option TypeSafe.Client)
  return fun state choices => do
    let path := directory / "usage.json"
    let budget : UsageBudget ← IO.ofExcept (Json.parse (← IO.FS.readFile path) >>= fromJson?)
    if budget.attempts >= maxRequests || budget.inputTokens >= maxInputTokens then
      blocked.set true
      throw <| IO.userError "run Jev usage budget exhausted"
    let reserved := { budget with
      attempts := budget.attempts + 1
      unknownUsage := budget.unknownUsage + 1 }
    writeJsonAtomic path (toJson reserved)
    let request := Scoring.request state choices config.model
    let start ← IO.monoMsNow
    let api ← match ← client.get with
      | some api => pure api
      | none => do
        let api ← (TypeSafe.Client.fromEnv {
          maxRetries := 0, timeoutSeconds := config.timeoutSeconds }).toIO
          (IO.userError ∘ toString)
        client.set (some api)
        pure api
    let outcome ← api.systemOneOutcome request
    let usage := outcome.reportedUsage.getD {}
    writeJsonAtomic path (toJson { reserved with
      inputTokens := reserved.inputTokens + usage.inputTokens.getD 0
      outputTokens := reserved.outputTokens + usage.outputTokens.getD 0
      unknownUsage := reserved.unknownUsage -
        if usage.inputTokens.isSome && usage.outputTokens.isSome then 1 else 0 })
    appendJson (directory / "decisions.jsonl") <| Json.mkObj [
      ("site", toJson site), ("method", toJson method), ("request", toJson request),
      ("elapsedMs", toJson ((← IO.monoMsNow) - start)),
      ("usage", toJson outcome.reportedUsage),
      ("response", match outcome.result with
        | .ok response => toJson response
        | .error error => Json.mkObj [("error", toJson (toString error))])]
    let response ← IO.ofExcept (outcome.result.mapError toString)
    Scoring.ranking response choices.size (state.getObjValD "independent_scores" == .bool true)

/-- Fisher–Yates without replacement, using a private, reproducibly seeded stream.
The search's existing sibling/ancestor deduplication is unchanged. -/
def randomOrder (size : Nat) (generator : StdGen) : Array Nat × StdGen := Id.run do
  let mut order := (List.range size).toArray
  let mut generator := generator
  for i in [:size] do
    let (j, next) := randNat generator i (size - 1)
    generator := next
    order := order.swapIfInBounds i j
  return (order, generator)

/-- Replace ranking decisions without altering search slots, refresh eligibility,
candidate generation or budgets. Local policies make no API requests. Legacy
`rankCalls` statistics count ranking decisions; usage.json counts API attempts. -/
def budgetedRanker (directory : System.FilePath) (site method : String)
    (config : JevHammer.Config) (maxRequests maxInputTokens : Nat)
    (mock : Bool) (blocked : IO.Ref Bool)
    (policy : String := "jev") (seed : Nat := 0) : IO Ranker := do
  unless #["jev", "fixed", "random"].contains policy do
    throw <| IO.userError "unknown ranking policy"
  if mock then
    unless policy == "jev" do throw <| IO.userError "mock and ranking policy are mutually exclusive"
    return ← jevRanker directory site method config maxRequests maxInputTokens true blocked
  let model ← if policy == "jev" then
    jevRanker directory site method config maxRequests maxInputTokens false blocked
    else pure fun _ choices => pure { order := (List.range choices.size).toArray }
  let generator ← IO.mkRef (mkStdGen (hash s!"jevbench-ranking-v1:{seed}:{site}").toNat)
  let invocation ← IO.mkRef (0 : Nat)
  return fun state choices => do
    let n ← invocation.get
    invocation.set (n + 1)
    let start ← IO.monoMsNow
    let base := Json.mkObj [
      ("site", toJson site), ("method", toJson method), ("policy", toJson policy),
      ("seed", toJson seed), ("invocation", toJson n), ("task", state.getObjValD "task"),
      ("choiceCount", toJson choices.size), ("stateHash", toJson (hash state.compress).toNat),
      ("choicesHash", toJson (hash (Json.arr choices).compress).toNat)]
    try
      let ranking ← if policy == "random" then do
        let (order, next) := randomOrder choices.size (← generator.get)
        generator.set next
        pure { order, model := "LOCAL-RANDOM" : Ranking }
      else if policy == "fixed" then
        pure { order := (List.range choices.size).toArray, model := "LOCAL-FIXED" : Ranking }
      else model state choices
      appendJson (directory / "rankings.jsonl") <| base.mergeObj <| Json.mkObj [
        ("order", toJson ranking.order), ("elapsedMs", toJson ((← IO.monoMsNow) - start))]
      return ranking
    catch error =>
      appendJson (directory / "rankings.jsonl") <| base.mergeObj <| Json.mkObj [
        ("error", toJson error.toString), ("elapsedMs", toJson ((← IO.monoMsNow) - start))]
      throw error

end JevHammerBenchmark
