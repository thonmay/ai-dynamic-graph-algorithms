# Related Work — Dynamic MCS Ordering Maintenance

Status: compiled 2026-09-21 from a live literature sweep (subagent-verified; see caveats at bottom).
Purpose: mandatory citations + novelty positioning for the paper.

## 1. Static MCS foundations
- Rose, Tarjan, Lueker 1976. "Algorithmic aspects of vertex elimination on directed graphs." SIAM J. Comput. 5(4):420-426. (Chordal recognition; PEO; MCS origin.)
- Tarjan, Yannakakis 1984. "A simple linear-time algorithm to test a graph for chordality and to find a chordal completion." SIAM J. Comput. 13(2):324-351. (Canonical linear-time MCS.)
- Berry, Blair, Heggernes, Peyton 2004. "Maximum cardinality search for computing minimal triangulations of graphs." Algorithmica 39(4):287-298. (MCS-M.)
- Spinrad 1993. Lexicographic BFS / Lex-M. (Minimal triangulation; related search paradigm.)

## 2. MCS structural problems (static decision problems — NOT maintenance)
- Rong, Cao, Wang, Wang 2022. "Graph searches and their end vertices." Algorithmica 84(9):2642-2666. (MCS end-vertex O(n^2) on chordal; NP-complete weakly chordal.)
- Rong, Yang, Li 2023. "A polynomial-time algorithm for MCS partial search order on chordal graphs." MFCS 2023, LIPIcs 247:77. (PSOP-MCS O(n^4) DP.)
- Rong, Yuan, Yang, Zhang 2026. "A linear-time algorithm for the MCS end-vertex problem on chordal graphs: A bonus-driven search strategy." SOSA 2026. (MCS-Ultra.)

## 3. Dynamic chordality / PEO maintenance (closest prior art)
- Ibarra 2008. "Fully dynamic algorithms for chordal graphs and split graphs." ACM Trans. Algorithms 4(4):40. (Fully dynamic, clique tree, O(n) per op. Notes maintaining a PEO under deletions+insertions "appears to be difficult.")
- Mezzini 2012. "Fully dynamic algorithm for chordal graphs with O(1) query-time and O(n^2) update-time." Theor. Comput. Sci. 445:82-92.
- Berry, Heggernes, Villanger 2006. "A vertex incremental approach for maintaining chordality." Discrete Math. 306(3):318-336. (Vertex-incremental O(1) query.)
- Banerjee, Raman, Satti 2018. "Maintaining chordal graphs dynamically: improved upper and lower bounds." CSR 2018, LNCS 10846:29-40. **(CLOSEST PRIOR ART: decremental-only, maintains SOME PEO by local common-neighbor move in O(deg), assumes graph stays chordal, lower bound Omega(log n) amortized cell-probe for dynamic chordality.)**
- Chandran, Ibarra, Ruskey, Sawada 2003. "Generating and characterizing the perfect elimination orderings of a chordal graph." Theor. Comput. Sci. 307:303-317. (Gray-code enumeration of all PEOs; constant-amortized-time transposition oracle — enumeration, not maintenance.)
- Semi-dynamic strongly-chordal 2020, arXiv:2002.07207.

## 4. Dynamic graph search (BFS/DFS/orderings)
- Even, Shiloach 1981. "On maintaining information in spite of bad communication." FOCS 1981. (ES trees: dynamic BFS baseline, O(mn) total.)
- Baswana, Choudhary, Khanna, Khan 2016. "Dynamic DFS in undirected graphs: breaking the O(m) barrier." SIAM J. Comput. 48(3). (first o(m) worst-case dynamic DFS; Omega(n) lower bound for explicitly-stored dynamic DFS trees.)
- Chen, Duan, Wang, Zhang, Zhang 2018. "An improved algorithm for incremental DFS tree in undirected graphs." SWAT 2018. (O(n) worst-case incremental DFS = matches lower bound; tree-partition + fractional cascading.)
- Nakamura, Sadakane 2019. "Space-efficient fully dynamic DFS in undirected graphs." Algorithms 12(3):52.
- Baswana, Gupta, Tulsyan 2019. MFCS 2019. (Overlapped periodic rebuilding: converts amortized to worst case; relevant to our complexity-reduction options.)

## 5. Lower bounds for dynamic problems
- Patrascu 2010. "Towards polynomial lower bounds for dynamic problems." STOC 2010.
- Demaine, Lopez-Ortiz, Munro 2004. "Lower bounds for dynamic connectivity." STOC 2004. (Omega(log n) cell-probe.)
- Henzinger, Krinninger, Nanongkai, Saranurak 2015. "Unifying and strengthening hardness for dynamic problems via the OMv conjecture." STOC 2015. (BFS/SSSP etc.)
- Abboud, Williams 2014. FOCS 2014. (BMM: no combinatorial poly improvement for dynamic BFS.)
- Jin, Xu 2022. STOC 2022. (Generalized k-Clique / OuMv.)
- Ramalingam, Reps 1996. "On the computational complexity of dynamic graph problems." Theor. Comput. Sci. (locally-persistent hierarchy.)
- No MCS-ordering-specific lower bound exists. Output-size argument: re-emitting an ordering after Theta(n) rank changes costs Omega(n) — conditional, not proven for MCS.

## 6. Formal verification of graph algorithms (Lean/Isabelle/Coq)
- Gueneau, Jourdan, Chargueraud, Pottier 2019. "Formal proof and analysis of an incremental cycle detection algorithm." ITP 2019, LIPIcs 141:18. **(CLOSEST verified dynamic graph data structure: Coq + CFML + SL with time credits; incremental (insertion-only) cycle detection; worst-case amortized complexity verified. NOT a search ordering.)**
- Bender, Fineman, Gilbert, Tarjan 2016. ACM Trans. Algorithms 12(2):14. (Unverified underlying algo.)
- Chargueraud, Pottier 2019. "Verifying the correctness and amortized complexity of a union-find implementation in separation logic with time credits." J. Autom. Reasoning 62(3):331-365.
- Wang, Cao, Mohan, Hobor 2019. "Certifying graph-manipulating C programs via localizations within data structures." POPL 2019. (VST/Coq, union-find from CompCert C.)
- Neumann 2015. "A framework for verifying depth-first search algorithms." CPP 2015. (Isabelle DFS framework.)
- Isabelle AFP "Elementary Graph Traversal Algorithms" (DFS/BFS verified, 2025 release).
- CLRS-Lean (Lean 4, 1218 kernel-checked theorems; Ch.21 union-find with O((m+n)alpha(n)) amortized; Ch.22 graph algorithms correctness-complete).
- Grandury, Nanevski, Gryzlov 2025. ICFP. (Schorr-Waite + union-find in Hoare Type Theory.)
- **No formalization of MCS, chordal graphs, or PEOs found in any proof assistant. No verified fully-dynamic search-ordering maintenance found. Our Lean 4 effort sits in an empty cell.**

## NOVELTY VERDICT
There is NO published result maintaining an MCS ordering (or any specific graph-search ordering) under edge updates. Closest = Banerjee et al. 2018 (decremental PEO via local moves, chordal-only, some PEO not the deterministic MCS order); Ibarra 2008 (fully dynamic chordality via clique tree, no ordering). Our contribution is novel on four axes:
1. fully dynamic (both insertions AND deletions) tracking the ordering itself,
2. maintains the SPECIFIC deterministic MCS ordering (smallest-id tie-break),
3. works for arbitrary undirected graphs (no chordality assumption needed),
4. local-probe-then-suffix-regreedy structure, machine-checked in Lean 4.

Distance from non-breakthrough: worst-case per update is O(n+m) = same as recompute; we do NOT prove sublinear worst case. The novelty is amortized efficiency + machine-checked correctness, not asymptotic worst-case improvement.

## CAVEATS
- Two negative claims ("no dynamic MCS maintenance"; "no verified MCS/PEO formalization") rest on strong but not exhaustive searches. Before the paper: harden with a targeted DBLP + Coq/Isabelle-AFP index sweep, and an arXiv API query on "dynamic MCS".
- Banerjee et al. journal version not retrieved (CSR 2018 proceedings + slides verified only).