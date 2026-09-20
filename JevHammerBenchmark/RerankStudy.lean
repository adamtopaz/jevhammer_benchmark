module
public meta import JevHammerBenchmark.Research
public meta section
namespace JevHammerBenchmark.RerankStudy

/-- CPU source selected by full-development coverage, then retrieval cost.
Structural variants own distinct caches from fixed synthetic initialization. -/
def cpuNative : Method := {
  Research.structuralPublic with
  config := { guidePremises := false }
  selectorName := "Public sparse + structural fusion, native premise order" }

def cpuReranked : Method := {
  cpuNative with
  selector := JevSelector.fuse #[Research.publicTarget.selector, Research.structuralSelector "rerank-cpu"] {}
  config := { guidePremises := true }
  warmup := do
    Research.publicTarget.warmup
    discard <| Research.structuralIndex "rerank-cpu"
  selectorName := "Public sparse + structural fusion, Jev premise reranking" }

def neuralNative : Method := {
  Research.structuralNeural with
  config := { guidePremises := false }
  selectorName := "Warmed neural + structural fusion, native premise order" }

def neuralReranked : Method := {
  neuralNative with
  selector := JevSelector.fuse #[Research.neuralWarm.selector, Research.structuralSelector "rerank-neural"] {}
  warmup := do
    Research.neuralWarm.warmup
    discard <| Research.structuralIndex "rerank-neural"
  config := { guidePremises := true }
  selectorName := "Warmed neural + structural fusion, Jev premise reranking" }

end JevHammerBenchmark.RerankStudy
