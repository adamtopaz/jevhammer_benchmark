import LeanHammerComparison

namespace LeanHammerFixture

theorem comparisonConjunction (p q : Prop) (h : p ∧ q) : q ∧ p := by
  exact ⟨h.2, h.1⟩
theorem comparisonIff (p q r : Prop) (h : p ↔ q) (k : q ↔ r) : p ↔ r := by
  exact h.trans k
theorem comparisonWitness (p : Nat → Prop) (h : p 3) : ∃ n, p n := by
  exact ⟨3, h⟩

end LeanHammerFixture
