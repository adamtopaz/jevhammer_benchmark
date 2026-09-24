import JevHammerBenchmark

open Lean JevHammerBenchmark

namespace StateRankingFixture

def method : Method := {
  selector := LibrarySuggestions.empty
  selectorName := "No premises: state-ranking integration fixture"
  tactics := {
    close := .fixed #["assumption"]
    cleanup := .fixed #["assumption"]
    steps := .fixed #["left", "right", "constructor"] }
  config := { maxMillis := 6000, maxCalls := 3, maxDepth := 3, beamWidth := 2 }
  tacticSetName := "Two distinct continuations followed by constructor/assumption" }

theorem branch (P Q : Prop) (hp : P) (hq : Q) : (P ∧ Q) ∨ (Q ∧ P) := by
  exact Or.inl ⟨hp, hq⟩

end StateRankingFixture
