import Mathlib

/-!
# Dynamic MCS ordering: crisp formalization (strategy H3, predicate shaping)

Same theorem as `ThesisLean/Formal_gen001c01_3939115c.lean`, full strength, no
added hypothesis.  The representation is reshaped so the loop invariant is
nearly syntactic: `neigh` is a filter cardinality, and the greedy completion is
a non-dependent accumulator (no proof argument baked into the loop), so the
induction carries no `proof_irrel` friction.
-/

noncomputable section
open Classical
open scoped BigOperators

namespace DynamicMCS

/-- Vertices of an `n`-vertex undirected graph. -/
abbrev Vert (n : ℕ) := Fin n

/-- A finite undirected, loop-free graph on the vertices `Fin n`. -/
structure UGraph (n : ℕ) where
  adj : Vert n → Vert n → Prop
  symm : ∀ {x y : Vert n}, adj x y → adj y x
  loopless : ∀ (x : Vert n), ¬ adj x x

namespace UGraph

variable {n : ℕ} {G G' : UGraph n}

/-- Number of neighbors of `w` lying in the already-chosen set `chosen`. -/
def neigh (G : UGraph n) (chosen : Finset (Vert n)) (w : Vert n) : ℕ :=
  (chosen.filter (fun x => G.adj w x)).card

/-- `w` is a legal MCS step given `chosen`: unchosen, of maximum cardinality
among the unchosen vertices, and least-index among those. -/
def IsMCSNext (G : UGraph n) (chosen : Finset (Vert n)) (w : Vert n) : Prop :=
  w ∈ (Finset.univ : Finset (Vert n)) \ chosen ∧
  (∀ x : Vert n, x ∈ (Finset.univ : Finset (Vert n)) \ chosen →
    G.neigh chosen x ≤ G.neigh chosen w) ∧
  (∀ x : Vert n, x ∈ (Finset.univ : Finset (Vert n)) \ chosen →
    G.neigh chosen x = G.neigh chosen w → w ≤ x)

/-- `order` is a valid MCS ordering of `G`. -/
def IsMCSOrdering (G : UGraph n) (order : List (Vert n)) : Prop :=
  order.Nodup ∧ order.length = n ∧
  ∀ (i : ℕ) (hi : i < order.length),
    IsMCSNext G (order.take i).toFinset (order.get ⟨i, hi⟩)

/-- The candidate's validity predicate on a state. -/
def ValidMCSState (G : UGraph n) (order : List (Vert n)) : Prop :=
  IsMCSOrdering G order

/-- `G'` differs from `G` only by flipping the undirected edge `{u, v}`. -/
def FlipOf (G G' : UGraph n) (u v : Vert n) : Prop :=
  u ≠ v ∧
  ∀ (x y : Vert n),
    G'.adj x y = G.adj x y ∨ (x = u ∧ y = v) ∨ (x = v ∧ y = u)

/-- Existence of a legal MCS pick when not every vertex is chosen. -/
theorem exists_IsMCSNext (G : UGraph n) (chosen : Finset (Vert n)) :
    chosen ≠ (Finset.univ : Finset (Vert n)) → ∃ w : Vert n, IsMCSNext G chosen w := by
  classical
  intro hneq
  let U : Finset (Vert n) := (Finset.univ : Finset (Vert n)) \ chosen
  have hUnonempty : U.Nonempty := by
    apply Finset.nonempty_iff_ne_empty.mpr
    intro hUempty
    apply hneq
    apply Finset.ext
    intro x
    constructor
    · intro _; exact Finset.mem_univ x
    · intro _hxuniv
      by_contra hx
      have hxempty : x ∈ (∅ : Finset (Vert n)) := by
        simpa [U, hUempty] using Finset.mem_sdiff.mpr ⟨Finset.mem_univ x, hx⟩
      exact (Finset.notMem_empty x) hxempty
  rcases Finset.exists_max_image U (fun x => G.neigh chosen x) hUnonempty with
    ⟨w0, hw0U, hw0max⟩
  let M : Finset (Vert n) := U.filter (fun x => G.neigh chosen x = G.neigh chosen w0)
  have hw0M : w0 ∈ M := Finset.mem_filter.mpr ⟨hw0U, rfl⟩
  have hMnonempty : M.Nonempty := ⟨w0, hw0M⟩
  let w : Vert n := M.min' hMnonempty
  refine ⟨w, ?_⟩
  have hwM : w ∈ M := Finset.min'_mem M hMnonempty
  have hwU : w ∈ U := (Finset.mem_filter.mp hwM).1
  have hwcard : G.neigh chosen w = G.neigh chosen w0 := (Finset.mem_filter.mp hwM).2
  unfold IsMCSNext
  refine ⟨by simpa [U] using hwU, ?_, ?_⟩
  · intro x hx
    rw [hwcard]
    exact hw0max x hx
  · intro x hx hc
    have hxM : x ∈ M := Finset.mem_filter.mpr ⟨hx, by rw [hc, hwcard]⟩
    exact Finset.min'_le M x hxM

/-- The deterministic MCS pick, carried with its legality proof. -/
noncomputable def greedyPick (G : UGraph n) (chosen : Finset (Vert n))
    (h : chosen ≠ (Finset.univ : Finset (Vert n))) : { w : Vert n // IsMCSNext G chosen w } :=
  ⟨Classical.choose (exists_IsMCSNext G chosen h),
   Classical.choose_spec (exists_IsMCSNext G chosen h)⟩

/-- Greedy completion: extend `chosen` with up to `k` MCS picks, stopping early
if every vertex is already chosen.  Non-dependent in `k`'s correctness proof. -/
def mcsLoop (G : UGraph n) (chosen : Finset (Vert n)) : ℕ → List (Vert n)
  | 0 => []
  | km + 1 =>
      if h : chosen = (Finset.univ : Finset (Vert n)) then []
      else (greedyPick G chosen h).1 :: mcsLoop G (insert (greedyPick G chosen h).1 chosen) km

/-- MCS continuation of an already-chosen set. -/
noncomputable def mcsRemainder (G : UGraph n) (chosen : Finset (Vert n)) : List (Vert n) :=
  mcsLoop G chosen (n - chosen.card)

/-- Greedy continuation of an MCS prefix `pref`. -/
noncomputable def greedySuffix (G : UGraph n) (pref : List (Vert n)) : List (Vert n) :=
  pref ++ mcsRemainder G pref.toFinset

/-- Position of the earlier of the endpoints `u` and `v`. -/
def earlierPos (order : List (Vert n)) (u v : Vert n) : ℕ :=
  min (List.idxOf u order) (List.idxOf v order)

/-- The candidate's dynamic update for an edge flip. -/
noncomputable def mcsUpdate (G : UGraph n) (u v : Vert n)
    (order : List (Vert n)) : List (Vert n) :=
  if _h : u = v then order
  else greedySuffix G (order.take (earlierPos order u v + 1))

/-! ## Lemmas -/

lemma le_idxOf_of_le_earlierPos (u v : Vert n) (order : List (Vert n))
    {i : ℕ} (hi : i ≤ earlierPos order u v) :
    i ≤ List.idxOf u order ∧ i ≤ List.idxOf v order := by
  unfold earlierPos at hi
  exact ⟨le_trans hi (Nat.min_le_left _ _), le_trans hi (Nat.min_le_right _ _)⟩

lemma endpoints_not_in_prefix (order : List (Vert n)) (u v : Vert n)
    (hmu : u ∈ order) (hmv : v ∈ order) {i : ℕ} (hi : i ≤ earlierPos order u v) :
    u ∉ order.take i ∧ v ∉ order.take i := by
  rcases le_idxOf_of_le_earlierPos u v order hi with ⟨hu, hv⟩
  rw [List.mem_take_iff_idxOf_lt hmu, List.mem_take_iff_idxOf_lt hmv]
  omega

lemma mem_of_IsMCSOrdering (order : List (Vert n)) (hvalid : IsMCSOrdering G order) :
    ∀ z : Vert n, z ∈ order := by
  classical
  intro z
  rcases hvalid with ⟨hnodup, hlen, _hstep⟩
  have hcard : order.toFinset.card = Fintype.card (Vert n) := by
    rw [List.toFinset_card_of_nodup hnodup, hlen]
    simp
  have htofinset : order.toFinset = (Finset.univ : Finset (Vert n)) :=
    Finset.eq_univ_of_card order.toFinset hcard
  rw [← List.mem_toFinset, htofinset]
  exact Finset.mem_univ z

lemma neigh_eq_of_flip (chosen : Finset (Vert n)) (u v : Vert n)
    (hflip : FlipOf G G' u v) (hu : u ∉ chosen) (hv : v ∉ chosen) :
    ∀ z : Vert n, G.neigh chosen z = G'.neigh chosen z := by
  classical
  intro z
  unfold neigh
  rcases hflip with ⟨_huv, hflipadj⟩
  apply congrArg Finset.card
  apply Finset.filter_congr
  intro x hxchosen
  rcases hflipadj z x with h | h' | h'
  · rw [← h]
  · rcases h' with ⟨rfl, rfl⟩; exact absurd hxchosen hv
  · rcases h' with ⟨rfl, rfl⟩; exact absurd hxchosen hu

lemma IsMCSNext_of_eq_neigh (chosen : Finset (Vert n)) (w : Vert n)
    (hneigh : ∀ z : Vert n, G.neigh chosen z = G'.neigh chosen z)
    (hnext : IsMCSNext G chosen w) : IsMCSNext G' chosen w := by
  classical
  rcases hnext with ⟨hwU, hwmax, hwmin⟩
  unfold IsMCSNext
  refine ⟨hwU, ?_, ?_⟩
  · intro x hx
    rw [← hneigh x, ← hneigh w]
    exact hwmax x hx
  · intro x hx hc
    exact hwmin x hx (by rw [hneigh x, hneigh w, hc])

lemma prefix_preserved (order : List (Vert n)) (u v : Vert n)
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order)
    (i : ℕ) (hi0 : i ≤ earlierPos order u v) (hi : i < order.length) :
    IsMCSNext G' (order.take i).toFinset (order.get ⟨i, hi⟩) := by
  classical
  have hstep := hvalid.2.2
  have hmu : u ∈ order := mem_of_IsMCSOrdering order hvalid u
  have hmv : v ∈ order := mem_of_IsMCSOrdering order hvalid v
  rcases endpoints_not_in_prefix order u v hmu hmv hi0 with ⟨hu, hv⟩
  have huF : u ∉ (order.take i).toFinset := fun h => hu (List.mem_toFinset.mp h)
  have hvF : v ∉ (order.take i).toFinset := fun h => hv (List.mem_toFinset.mp h)
  have hneigh : ∀ z : Vert n, G.neigh (order.take i).toFinset z =
      G'.neigh (order.take i).toFinset z :=
    fun z => neigh_eq_of_flip (order.take i).toFinset u v hflip huF hvF z
  exact IsMCSNext_of_eq_neigh (order.take i).toFinset (order.get ⟨i, hi⟩) hneigh (hstep i hi)

lemma prefix_valid_append (pref : List (Vert n)) (p : Vert n)
    (hpref : ∀ (i : ℕ) (hi : i < pref.length),
      IsMCSNext G (pref.take i).toFinset (pref.get ⟨i, hi⟩))
    (hp : IsMCSNext G pref.toFinset p) :
    ∀ (i : ℕ) (hi : i < (pref ++ [p]).length),
      IsMCSNext G ((pref ++ [p]).take i).toFinset ((pref ++ [p]).get ⟨i, hi⟩) := by
  intro i hi
  by_cases hlt : i < pref.length
  · have htake : (pref ++ [p]).take i = pref.take i := by
      rw [List.take_append, Nat.sub_eq_zero_of_le (le_of_lt hlt)]
      simp
    have hget : (pref ++ [p]).get ⟨i, hi⟩ = pref.get ⟨i, hlt⟩ := by
      apply List.getElem_append_left
    rw [htake, hget]
    exact hpref i hlt
  · have hi_eq : i = pref.length := by
      have : (pref ++ [p]).length = pref.length + 1 := by simp
      rw [this] at hi
      omega
    subst i
    have htake : (pref ++ [p]).take pref.length = pref := by
      rw [List.take_append]; simp
    have hget : (pref ++ [p]).get ⟨pref.length, hi⟩ = p := by
      simp [List.get_eq_getElem, List.getElem_append_right (le_refl pref.length)]
    rw [htake, hget]
    exact hp

/-- Loop invariant: a valid MCS prefix `pref` whose chosen set is `chosen`,
extended by `mcsLoop G chosen k`, is a valid MCS ordering whenever
`chosen.card + k = n`.  Induction on `k`; the accumulator shape means the
`chosen = univ` branch is vacuous in the step, so no proof-argument friction. -/
lemma mcsLoop_valid :
    ∀ (k : ℕ) (chosen : Finset (Vert n)), chosen.card + k = n →
      ∀ (pref : List (Vert n)), pref.toFinset = chosen → pref.Nodup →
        (∀ (i : ℕ) (hi : i < pref.length),
          IsMCSNext G (pref.take i).toFinset (pref.get ⟨i, hi⟩)) →
        IsMCSOrdering G (pref ++ mcsLoop G chosen k) := by
  intro k
  induction k with
  | zero =>
      intro chosen hk pref hprefF hprefNodup hpref
      have : mcsLoop G chosen 0 = [] := rfl
      rw [this, List.append_nil]
      refine ⟨hprefNodup, ?_, hpref⟩
      have hcard : chosen.card = n := by rw [add_zero] at hk; exact hk
      calc pref.length = pref.toFinset.card := (List.toFinset_card_of_nodup hprefNodup).symm
        _ = chosen.card := by rw [hprefF]
        _ = n := hcard
  | succ km ih =>
      intro chosen hk pref hprefF hprefNodup hpref
      have hchosen : chosen ≠ (Finset.univ : Finset (Vert n)) := by
        intro hc
        have hcard : chosen.card = n := by simp [hc]
        omega
      set p := (greedyPick G chosen hchosen).1 with hpdef
      have hp : p ∉ chosen :=
        (Finset.mem_sdiff.mp (greedyPick G chosen hchosen).2.1).2
      have hrec : (insert p chosen).card + km = n := by
        have hins : (insert p chosen).card = chosen.card + 1 :=
          Finset.card_insert_of_notMem hp
        omega
      have hstep : mcsLoop G chosen (km + 1) = p :: mcsLoop G (insert p chosen) km := by
        show (if h : chosen = (Finset.univ : Finset (Vert n)) then []
              else (greedyPick G chosen h).1 ::
                mcsLoop G (insert (greedyPick G chosen h).1 chosen) km) = _
        rw [dite_eq_right hchosen]
      rw [hstep, ← List.singleton_append, ← List.append_assoc]
      refine ih (insert p chosen) hrec (pref ++ [p]) ?F ?N ?S
      · apply Finset.ext
        intro x
        rw [List.mem_toFinset, List.mem_append, List.mem_singleton, Finset.mem_insert,
          ← hprefF, ← List.mem_toFinset]
        exact ⟨fun h => h.elim Or.inr Or.inl, fun h => h.elim Or.inr Or.inl⟩
      · rw [List.nodup_append]
        refine ⟨hprefNodup, List.nodup_singleton p, ?_⟩
        intro a ha b hb
        rw [List.mem_singleton] at hb
        subst hb
        intro heq
        exact hp (by rw [← hprefF]; exact List.mem_toFinset.mpr (heq ▸ ha))
      · refine prefix_valid_append pref p hpref ?_
        rw [hprefF]
        exact (greedyPick G chosen hchosen).2

/-- Recombining a valid MCS prefix with the greedy suffix yields a valid MCS
ordering of the same graph. -/
lemma greedySuffix_valid (G : UGraph n) (pref : List (Vert n)) (hnodup : pref.Nodup)
    (hstep : ∀ (i : ℕ) (hi : i < pref.length),
      IsMCSNext G (pref.take i).toFinset (pref.get ⟨i, hi⟩)) :
    IsMCSOrdering G (greedySuffix G pref) := by
  unfold greedySuffix mcsRemainder
  refine mcsLoop_valid (n - pref.toFinset.card) pref.toFinset ?_ pref rfl hnodup hstep
  have hcard : pref.toFinset.card ≤ n := by
    have : Fintype.card (Vert n) = n := by simp [Vert]
    simpa [this] using Finset.card_le_univ pref.toFinset
  omega

/-! ## Theorems -/

theorem mcsUpdate_preserves_invariant (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    IsMCSOrdering G' (mcsUpdate G' u v order) := by
  classical
  have huv : u ≠ v := hflip.1
  have hmemu : u ∈ order := mem_of_IsMCSOrdering order hvalid u
  rw [mcsUpdate, dite_eq_right huv]
  have hbound : earlierPos order u v + 1 ≤ order.length := by
    unfold earlierPos
    have hpos : List.idxOf u order < order.length := List.idxOf_lt_length_of_mem hmemu
    omega
  refine greedySuffix_valid G' (order.take (earlierPos order u v + 1))
    (List.Pairwise.take hvalid.1) ?S
  intro i hi
  have hlt : i < order.length :=
    Nat.lt_of_lt_of_le (Nat.lt_of_lt_of_le hi (List.length_take_le _ _)) hbound
  have hi0 : i ≤ earlierPos order u v :=
    Nat.lt_succ_iff.mp (Nat.lt_of_lt_of_le hi (List.length_take_le _ _))
  have htake : (order.take (earlierPos order u v + 1)).take i = order.take i := by
    rw [List.take_take, Nat.min_eq_left (Nat.le_succ_of_le hi0)]
  have hget : (order.take (earlierPos order u v + 1)).get ⟨i, hi⟩
      = order.get ⟨i, hlt⟩ := by
    rw [List.get_eq_getElem, List.get_eq_getElem, List.getElem_take]
  rw [htake, hget]
  exact prefix_preserved order u v hflip hvalid i hi0 hlt

theorem insert_edge_valid (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    ValidMCSState G' (mcsUpdate G' u v order) := by
  exact mcsUpdate_preserves_invariant u v order hflip hvalid

theorem delete_edge_valid (u v : Vert n) (order : List (Vert n))
    (hflip : FlipOf G G' u v) (hvalid : IsMCSOrdering G order) :
    ValidMCSState G' (mcsUpdate G' u v order) := by
  exact mcsUpdate_preserves_invariant u v order hflip hvalid

theorem init_valid (G : UGraph n) : ValidMCSState G (greedySuffix G []) := by
  unfold ValidMCSState
  refine greedySuffix_valid G [] List.nodup_nil ?_
  intro i hi
  rw [List.length_nil] at hi
  exact absurd hi (Nat.not_lt_zero i)

end UGraph
end DynamicMCS
