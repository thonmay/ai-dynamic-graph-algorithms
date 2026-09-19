import ThesisLean.Formal_gen001c01_3939115c

/-!
# Crisp dynamic-MCS correctness by hypothesis decomposition (strategy H1)

The full proof (480 lines, `ThesisLean/Formal_gen001c01_3939115c.lean`) of
`mcsUpdate_preserves_invariant` contains exactly two mathematical ideas:

1. **Prefix preservation.**  Flipping the edge `{u, v}` changes a vertex's
   cardinality only once one of its endpoints is already chosen, so every
   greedy pick up to and including the earlier endpoint is unchanged on the
   post-update graph `G'`.
2. **Greedy extension.**  Appending the deterministically recomputed greedy
   suffix to a valid MCS prefix yields a valid MCS ordering.

This module takes (1) as a single named hypothesis, `PrefixPreserved`, and
proves the real correctness statement `IsMCSOrdering G' (mcsUpdate G' u v order)`
from it in a few lines.  Note what the decomposition consumes: the entire
edge-flip structure `FlipOf G G' u v` is used *only* to establish prefix
preservation; the crisp theorem needs nothing of it except `u ≠ v`.
-/

open Classical

namespace DynamicMCS.UGraph

variable {n : ℕ} {G G' : UGraph n}

/-- **Prefix preservation** (the H1 hypothesis): after the update to `G'`,
every position of the old ordering `order` up to and including the earlier of
the endpoints `u`, `v` is still the legal MCS pick (max cardinality, lowest
index) given the vertices chosen before it. -/
def PrefixPreserved (G' : UGraph n) (order : List (Vert n)) (u v : Vert n) : Prop :=
  ∀ (i : ℕ) (hi : i < order.length),
    i ≤ earlierPos order u v →
    IsMCSNext G' (order.take i).toFinset (order.get ⟨i, hi⟩)

/-- **Crisp dynamic MCS correctness.**  Given prefix preservation, the
candidate's update `mcsUpdate` (keep the prefix through the earlier endpoint,
recompute the greedy suffix on `G'`) returns a valid MCS ordering of `G'`.
This is the full invariant-preservation theorem modulo the prefix-preservation
hypothesis: the flip relation `FlipOf` and the pre-update validity
`IsMCSOrdering G order` appear nowhere in the statement. -/
theorem crisp_mcs_update_valid (u v : Vert n) (order : List (Vert n))
    (huv : u ≠ v) (hnodup : order.Nodup)
    (hprefix : PrefixPreserved G' order u v) :
    IsMCSOrdering G' (mcsUpdate G' u v order) := by
  classical
  rw [mcsUpdate, dite_eq_right huv]
  refine greedySuffix_valid G' (order.take (earlierPos order u v + 1))
    (List.Pairwise.take hnodup) ?_
  intro i hi
  -- `i` lies inside the kept prefix, hence before the earlier endpoint.
  have hlt : i < order.length :=
    Nat.lt_of_lt_of_le hi (by rw [List.length_take]; exact Nat.min_le_right _ _)
  have hki : i ≤ earlierPos order u v :=
    Nat.lt_succ_iff.mp (Nat.lt_of_lt_of_le hi
      (by rw [List.length_take]; exact Nat.min_le_left _ _))
  -- Taking the prefix of a prefix: the kept prefix agrees with `order`.
  have htake : (order.take (earlierPos order u v + 1)).take i = order.take i := by
    rw [List.take_take, Nat.min_eq_left (Nat.le_succ_of_le hki)]
  have hget : (order.take (earlierPos order u v + 1)).get ⟨i, hi⟩
      = order.get ⟨i, hlt⟩ := by
    rw [List.get_eq_getElem, List.get_eq_getElem, List.getElem_take]
  rw [htake, hget]
  exact hprefix i hlt hki

/-- **The decomposition is complete.**  The full theorem
`mcsUpdate_preserves_invariant` of the 480-line file is exactly the crisp
theorem applied to the prefix-preservation lemma `prefix_preserved`: no other
part of the flip structure is needed. -/
theorem mcsUpdate_valid_of_crisp (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    IsMCSOrdering G' (mcsUpdate G' u v order) := by
  refine crisp_mcs_update_valid u v order hflip.1 hvalid.1 ?_
  intro i hi hle
  exact prefix_preserved order u v hflip hvalid i hle hi

#print axioms DynamicMCS.UGraph.crisp_mcs_update_valid
#print axioms DynamicMCS.UGraph.mcsUpdate_valid_of_crisp

end DynamicMCS.UGraph
