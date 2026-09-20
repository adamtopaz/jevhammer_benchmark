module
public meta import JevHammerBenchmark.RerankStudy
public meta section
namespace JevHammerBenchmark.RewriteStudy
open Lean Meta LibrarySuggestions

initialize rewriteBaseCache : IO.Ref (Option JevSelector.StructuralIndex) ← IO.mkRef none
initialize rewriteMethodCaches : IO.Ref (Std.HashMap String JevSelector.StructuralIndex) ← IO.mkRef {}

def rewriteIndex (key : String) : MetaM JevSelector.StructuralIndex := do
  if let some idx := (← rewriteMethodCaches.get)[key]? then return idx
  let base ← match ← rewriteBaseCache.get with
    | some idx => pure idx
    | none => do
      let idx ← JevSelector.StructuralIndex.create .rewrites
      idx.warmup
      rewriteBaseCache.set (some idx)
      pure idx
  let idx ← base.freshCache
  rewriteMethodCaches.modify (·.insert key idx)
  return idx

def rewriteSelector (key : String) : Selector := fun goal cfg => do
  (← rewriteIndex key).selector {} goal cfg

def rewriteProvenance (owners : Array Name) : MetaM Json := pure <| Json.mkObj [
  ("kind", toJson "bounded-equality-iff-signature-subexpressions"),
  ("proofTraining", toJson "none"), ("fittedStatistics", toJson "none"),
  ("evaluationOwners", toJson owners.size), ("queryHeartbeats", toJson (10000 : Nat)),
  ("maxNodes", toJson (256 : Nat)), ("maxQueries", toJson (64 : Nat)),
  ("maxDepth", toJson (8 : Nat)), ("maxHypotheses", toJson (8 : Nat)),
  ("cachePolicy", toJson "independent per-method caches from fixed True warmup")]

def cpuControl : Method := { RerankStudy.cpuNative with
  selectorName := "Public sparse + conclusion patterns, native premise order" }

def cpuRewrites : Method := {
  cpuControl with
  selector := JevSelector.fuse #[Research.publicTarget.selector,
    Research.structuralSelector "rewrite-cpu", rewriteSelector "cpu"] {}
  selectorName := "Public sparse + conclusion + rewrite patterns, native premise order"
  warmup := do
    Research.publicTarget.warmup
    discard <| Research.structuralIndex "rewrite-cpu"
    discard <| rewriteIndex "cpu"
  validate := fun owners => do
    return Json.mkObj [("control", ← cpuControl.validate owners),
      ("rewrites", ← rewriteProvenance owners)] }

def signatureOnly : Method := {
  cpuControl with
  selector := JevSelector.fuse #[Research.structuralSelector "rewrite-signature-only",
    rewriteSelector "signature-only"] {}
  selectorName := "Conclusion + rewrite patterns, no fitted artifact, native premise order"
  warmup := do
    discard <| Research.structuralIndex "rewrite-signature-only"
    discard <| rewriteIndex "signature-only"
  validate := fun owners => do
    return Json.mkObj [("conclusions", ← Research.structuralProvenance owners),
      ("rewrites", ← rewriteProvenance owners)] }

def neuralControl : Method := { RerankStudy.neuralReranked with
  selectorName := "Warmed neural + conclusion patterns, Jev premise reranking" }

def neuralRewrites : Method := {
  neuralControl with
  selector := JevSelector.fuse #[Research.neuralWarm.selector,
    Research.structuralSelector "rewrite-neural", rewriteSelector "neural"] {}
  selectorName := "Warmed neural + conclusion + rewrite patterns, Jev premise reranking"
  warmup := do
    Research.neuralWarm.warmup
    discard <| Research.structuralIndex "rewrite-neural"
    discard <| rewriteIndex "neural"
  validate := fun owners => do
    return Json.mkObj [("control", ← neuralControl.validate owners),
      ("rewrites", ← rewriteProvenance owners)] }

end JevHammerBenchmark.RewriteStudy
