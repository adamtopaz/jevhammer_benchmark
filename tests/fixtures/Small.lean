import Mathlib.Data.Nat.Basic

namespace BenchmarkFixture

theorem identity (p : Prop) (h : p) : p := by
  exact h

theorem conjunction (p q : Prop) (hp : p) (hq : q) : p ∧ q := by
  constructor
  · exact hp
  · exact hq

theorem arithmetic (a b : Nat) (h : a < b) : a + 1 ≤ b := by
  omega

theorem later (p : Prop) (h : p) : p := by
  exact identity p h

end BenchmarkFixture

namespace BenchmarkUniverses

theorem reflexive {α : Sort u} (a : α) : a = a := by
  rfl

theorem withLet (n : Nat) : n + 0 = n := by
  let m := n
  change m + 0 = m
  simp

end BenchmarkUniverses

namespace BenchmarkPrivate

private theorem previous (p : Prop) (hp : p) : p := by
  exact hp

theorem usingPrevious (p : Prop) (hp : p) : p := by
  exact previous p hp

end BenchmarkPrivate
