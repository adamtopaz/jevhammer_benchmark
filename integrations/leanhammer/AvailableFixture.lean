namespace AvailableFixture
def marker (n : Nat) : Prop := n = n
theorem first (n : Nat) : marker n := rfl
theorem heldout (n : Nat) : marker n := first n
theorem heldout.child (n : Nat) : marker n := first n
theorem later (n : Nat) : marker n := heldout n
end AvailableFixture
