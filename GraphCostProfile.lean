import Mathlib
import JevHammerBenchmark.GraphStudy

open Lean Meta Elab Command LibrarySuggestions JevSelector JevHammerBenchmark
set_option maxHeartbeats 0
set_option Elab.async false

-- CPU-only diagnostics on fixed public statement types, not held-out proof goals.
-- Inject deterministic directions; no Jev or neural service is called.
run_cmd liftTermElabM do
  let _ : MonadExceptOf Exception MetaM :=
    { (inferInstance : MonadExceptOf Exception MetaM) with tryCatch := tryCatchRuntimeEx }
  let _ : MonadExceptOf Exception TermElabM :=
    { (inferInstance : MonadExceptOf Exception TermElabM) with tryCatch := tryCatchRuntimeEx }
  let some path ← IO.getEnv "JEVSELECTOR_GRAPH_PROFILE_OUTPUT"
    | throwError "missing graph profile output"
  let previewText := (← IO.getEnv "JEVSELECTOR_GRAPH_PROFILE_PREVIEW_CANDIDATES").getD "0"
  let some previewCount := previewText.toNat?
    | throwError "graph preview count must be a nonnegative integer"
  let graphOptions := { GraphStudy.graphOptions with maxPreviewCandidates := previewCount }
  let phase : String → IO Unit := fun name => do
    let log ← IO.FS.Handle.mk (path ++ ".phases.jsonl") .append
    log.putStrLn (Json.mkObj [("phase", toJson name), ("monoMs", toJson (← IO.monoMsNow))]).compress
    log.flush
    IO.eprintln s!"Graph profile phase: {name}"
  phase "loading"
  let loadStart ← IO.monoMsNow
  let idx ← Research.publicIndex
  let loadMs := (← IO.monoMsNow) - loadStart
  IO.eprintln s!"Graph profile: statement index loaded in {loadMs}ms; validating environment"
  phase "validation"
  let validationStart ← IO.monoMsNow
  idx.validateEnvironment
  let validationMs := (← IO.monoMsNow) - validationStart
  IO.eprintln s!"Graph profile: validation completed in {validationMs}ms; building graph"
  phase "graph"
  let graphStart ← IO.monoMsNow
  let graph ← DependencyGraph.create
  let graphInitMs := (← IO.monoMsNow) - graphStart
  IO.eprintln s!"Graph initialized: {graph.entries.size} signatures in {graphInitMs}ms"
  phase "structural"
  let shapeStart ← IO.monoMsNow
  let shape ← StructuralIndex.create
  shape.warmup
  let shapeInitMs := (← IO.monoMsNow) - shapeStart
  phase "queries"
  let mut rows := #[]
  let count := min 32 idx.artifact.declarations.size
  for mode in #["base", "none", "forward", "backward"] do
    let independentShape ← shape.freshCache
    let base := fuse #[idx.targetSelector, independentShape.selector {}] {}
    for i in [:count] do
      let e := idx.artifact.declarations[i * idx.artifact.declarations.size / count]!
      let name := e.name.toName
      let some info := (← getEnv).findConstVal? name | continue
      for repetition in [:3] do
        let saved ← saveState
        try
          let goal ← mkFreshExprMVar info.type
          let calls ← IO.mkRef (0 : Nat)
          let choiceCount ← IO.mkRef (0 : Nat)
          let payloadBytes ← IO.mkRef (0 : Nat)
          let rank : GraphRanker := fun question _ choices => do
            calls.modify (· + 1)
            choiceCount.modify (· + choices.size)
            payloadBytes.modify (· + question.utf8ByteSize + (Json.arr choices).compress.utf8ByteSize)
            let indices := (List.range choices.size).toArray
            let first := indices.filter fun j => choices[j]!.getObjValD "direction" == .str mode
            return first ++ indices.filter (fun j => !first.contains j)
          let select := if mode == "base" then base else graph.guided graphOptions rank base
          let start ← IO.monoNanosNow
          let mut error := ""
          let suggestions ← try
            select goal.mvarId! { maxSuggestions := 100, filter := fun n => pure (n != name) }
          catch ex =>
            error ← ex.toMessageData.toString
            pure #[]
          let elapsed := (← IO.monoNanosNow) - start
          rows := rows.push <| Json.mkObj [("mode", toJson mode), ("name", toJson e.name),
            ("repeat", toJson repetition), ("elapsedNanos", toJson elapsed),
            ("returned", toJson suggestions.size), ("rankCalls", toJson (← calls.get)),
            ("choices", toJson (← choiceCount.get)), ("choiceBytes", toJson (← payloadBytes.get)),
            ("error", toJson error), ("suggestions", toJson (suggestions.map (·.name.toString)))]
          -- Persist partial diagnostics even if a later query times out.
          IO.FS.writeFile path <| (Json.mkObj [("schema", toJson (1 : Nat)),
            ("kind", toJson "cpu-only-graph-cost"), ("loadMs", toJson loadMs),
            ("previewCandidates", toJson previewCount),
            ("validationMs", toJson validationMs),
            ("graphInitMs", toJson graphInitMs), ("shapeInitMs", toJson shapeInitMs),
            ("graphEntries", toJson graph.entries.size), ("modelCalls", toJson (0 : Nat)),
            ("proofTrials", toJson (0 : Nat)), ("queries", .arr rows)]).compress
          IO.eprintln s!"Graph profile {mode} query {i} repeat {repetition}: {elapsed / 1000000}ms, error={ !error.isEmpty }"
        finally saved.restore
  phase "complete"
