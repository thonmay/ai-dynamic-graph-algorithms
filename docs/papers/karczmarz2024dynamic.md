# karczmarz2024dynamic

*Source: karczmarz2024dynamic.pdf*
*Pages: 26*

## Page 1

### arXiv:2406.10420v1  [cs.DS]  14 Jun 2024
### Fully Dynamic Strongly Connected Components in Planar Digraphs
Adam Karczmarz∗
Marcin Smulewicz†
**Abstract**
In this paper, we consider maintaining strongly connected components (SCCs) of a directed
planar graph subject to edge insertions and deletions. We show a data structure maintaining
an implicit representation of the SCCs within �O(n6/7) worst-case time per update. The data
structure supports, in O(log2 n) time, reporting vertices of any speciﬁed SCC (with constant
overhead per reported vertex) and aggregating vertex information (e.g., computing the maximum
label) over all the vertices of that SCC. Furthermore, it can maintain global information about
the structure of SCCs, such as the number of SCCs, or the size of the largest SCC.
To the best of our knowledge, no fully dynamic SCCs data structures with sublinear update
time have been previously known for any major subclass of digraphs. Our result should be con-
trasted with the n1−o(1) amortized update time lower bound conditional on SETH [AW14], which
holds even for dynamically maintaining whether a general digraph has more than two SCCs.
#### 1
#### Introduction
Two vertices of a directed graph G = (V, E) are called strongly connected if they can reach each
other using paths in G. Pairwise strong connectivity is an equivalence relation and the strongly
connected components (SCCs) of G are its equivalence classes. Computing the SCCs is among
the most classical and fundamental algorithmic problems on digraphs and there exists a number of
linear-time algorithms for that [Gab00, Sha81, Tar72]. Therefore, it is no surprise that maintaining
SCCs has been one of the most actively studied problems on dynamic directed graphs [AW14,
BFGT16, BDP21, BGS20, BPW19, CHI+16, CKL+23, HKM+12, IKŁS17, KS23, Łą13, RZ08].
When maintaining the strongly connected components, the information we care about may
vary. First, we could be interested in eﬃciently answering pairwise strong connectivity queries:
given u, v ∈V , decide whether u and v are strongly connected.
Pairwise strong connectivity
queries, however, cannot easily provide any information about the global structure of SCCs (such
as the number of SCCs, the size of the largest SCC). Neither they enable, e.g., listing the vertices
strongly connected to some u ∈V . This is why, in the following, we distinguish between dynamic
pairwise strong connectivity and dynamic SCCs data structures which provide a more global view.
In particular, all the data about the SCCs can be easily accessed if the SCCs are maintained
explicitly, e.g., if the SCC identiﬁer of every vertex is stored at all times and explicitly updated.
**1.1**
**Previous work**
In the following, let n = |V | and m = |E|. Dynamic graph data structures are traditionally stud-
ies in incremental, decremental or fully dynamic settings, which permit the graph to evolve by
either only edge insertions, only deletions, or both, respectively.
A decremental data structure
∗University of Warsaw and IDEAS NCBR, Poland. a.karczmarz@mimuw.edu.pl. Partially supported by the ERC
CoG grant TUgbOAT no 772346 and the National Science Centre (NCN) grant no. 2022/47/D/ST6/02184.
†University of Warsaw, Poland. m.smulewicz@mimuw.edu.pl
1

## Page 2

maintaining SCCs with near-optimal total update time is known [BPW19]. Very recently, a deter-
ministic data structure with m1+o(1) total update time has been obtained also for the incremental
setting [CKL+23]. Both these state-of-the art data structures maintain the SCCs explicitly.
The fully dynamic variant – which is our focus in this paper – although the most natural, has
been studied the least. First of all, there is strong evidence that a non-trivial dynamic SCCs data
structure for sparse graphs cannot exist.
If the SCCs have to be maintained explicitly, then a
single update can cause a rather dramatic Ω(n)-sized amortized change in the set of SCCs1. As
a result, an explicit update may be asymptotically as costly as recomputing SCCs from scratch.
This argument – applicable also for maintaining connected components of an undirected graph –
does not exclude the possibility of maintaining an implicit representation of the SCCs in sublin-
ear time, though. After all, there exist very eﬃcient fully dynamic connectivity data structures,
e.g., [HdLT01, HHK+23, Wul13], typically maintaining also an explicit spanning forest which al-
lows retrieving any “global” component-wise information one can think of rather easily.
How-
ever, [AW14] showed that even for maintaining a single-bit information whether G has more than
two SCCs, a data structure with O(n1−ǫ) amortized time is unlikely, as it would break the Orthog-
onal Vectors conjecture implied by the SETH [IP01, Wil05].2 This considerably limits the possible
global information about the SCCs that can be maintained within sublinear time per update.
For denser graphs, [AW14] also proved that maintaining essentially any (even pairwise) informa-
tion about SCCs dynamically within truly subquadratic update time has to rely on fast matrix mul-
tiplication. And indeed, that pairwise strong connectivity can be maintained this way follows easily
from the dynamic matrix inverse-based dynamic st-reachability data structures [vdBNS19, San05].
More recently, [KS23] showed that in fact SCCs can be maintained explicitly in O(n1.529) worst-case
time per update. They also proved that maintaining whether G has just a single SCC (dynamic SC)
is easier3 and can be achieved within O(n1.406) worst-case time per update. Both these bounds are
tight conditional on the appropriate variants [vdBNS19] of the OMv conjecture [HKNS15].
In summary, the complexity of maintaining SCCs in general directed graphs is rather well-
understood now. In partially dynamic settings, the known bounds are near optimal unconditionally,
whereas in the fully dynamic setting, the picture appears complete unless some popular hardness
conjectures are proven wrong. In particular, for general sparse digraphs, no (asymptotically) non-
trivial fully dynamic SCCs data structure can exist.
Planar graphs.
It is thus natural to ask whether non-trivial dynamic SCCs data structures are
possible if we limit our attention to some signiﬁcant class of sparse digraphs. And indeed, this
question has been partially addressed for planar digraphs in the past. Since pairwise s, t-strong
connectivity queries reduce to two s, t-reachability queries, the known planar dynamic reachability
data structures [DS07, Sub93] imply that sublinear ( �O(n2/3) or �O(√n)-time, depending on whether
embedding-respecting insertions are required) updates/queries are possible for pairwise strong con-
nectivity. Another trade-oﬀfor dynamic pairwise strong connectivity has been showed by [CK22].
Namely, they showed a fully dynamic data structure for planar graphs with �O(n4/5) worst-case up-
date time that can produce an identiﬁer sv of an SCC of a given query vertex v in O(log2 n) time.
Whereas this is slightly more general4, it still not powerful enough to enable eﬃciently maintaining
any of the global data about the SCCs of a dynamic planar digraph such as the SCCs count.
1Consider a directed cycle and switching its arbitrary single edge on and oﬀ.
2In [AW14], a conditional lower bound of the same strength is also derived for the dynamic #SSR problem where
the goal is to dynamically count vertices reachable from a source s ∈V .
3Interestingly, the SETH-based lower bound of [AW14] does not apply to the dynamic SC problem.
4Than answering pairwise strong connectivity queries. Using the SCC-identiﬁers, one can, e.g., partition any k
vertices of G into strongly connected classes in �O(k) time, whereas using pairwise queries this requires Θ(k2) queries.
2

## Page 3

To the best of our knowledge, the question whether a more robust – that is, giving a more
“global” perspective on the SCCs beyond only supporting pairwise queries – fully dynamic SCCs
data structure for planar digraphs (or digraphs from any other interesting class) with sublinear
update time is possible has not been addressed before.
**1.2**
**Our results**
In this paper, we address the posed question in the case of planar directed graphs. Speciﬁcally, our
main result is a dynamic SCCs data structure summarized by the following theorem.
**Theorem 1.1. Let G be a planar digraph subject to planarity-preserving edge insertions and dele-**
tions. There exists a data structure maintaining the strongly connected components of G implicitly
in �O(n6/7) worst-case time per update. Speciﬁcally:
• The data structure maintains the number of SCCs and the size of the largest SCC in G.
• For any query vertex v, in O(log2 n) time the data structure can compute the size of the SCC
of v, and enable reporting the elements of the SCC of v in O(1) worst-case time per element.
In particular, Theorem 1.1 constitutes the ﬁrst known fully dynamic SCCs data structure with
sublinear update time for any signiﬁcant class of sparse digraphs. It also shows that the conditional
lower bound of [AW14] does not hold in planar digraphs.
The data structure of Theorem 1.1 is deterministic and does not require the edge insertions
to respect any ﬁxed embedding of the graph (this also applies to side results discussed below).
Obtaining more eﬃcient data structures for fully dynamic embedding-respecting updates is an
interesting direction (see, e.g., [DS07]) that is beyond the scope of this paper.
Related problems.
Motivated by the discrepancies between the known bounds for dynamic
SCCs and dynamic SC in general digraphs (both from the lower- [AW14] and upper bounds [KS23]
perspective), we also complement Theorem 1.1 with a signiﬁcantly simpler and faster data structure
suggesting that the dynamic SC might be easier (than dynamic SCCs) in planar digraphs as well.5
**Lemma 1.2. Let G be a planar digraph subject to planarity-preserving edge insertions and dele-**
tions. One can maintain whether G has a single SCC in �O(n2/3) worst-case time per update.
Similarly, one could ask how dynamic #SSR (i.e., counting vertices reachable from a single
source) relates to dynamic SCCs in planar digraphs. Especially since:
(1) in general directed graphs, dynamic SCCs and dynamic #SSR currently have matching lower-
[AW14, vdBNS19] and upper bounds [KS23, San05] (up to polylogarithmic factors);
(2) the former problem is at least as hard as the latter in the sense that dynamic #SSR reduces
to dynamic SCCs in general graphs easily6, whereas an opposite reduction is not known.
Unfortunately, the aforementioned reduction of dynamic #SSR to dynamic SCCs breaks planarity
rather badly. Interestingly, the path net technique we develop to obtain Theorem 1.1 does not seem
to work for counting “asymmetric” reachabilities from a single source.
Nevertheless, we observe that the Voronoi diagram machinery developed for computing the
diameter of a planar graph [GKM+21] almost immediately yields a more eﬃcient data structure for
5Clearly, one could use Theorem 1.1 for dynamic SC as well.
6Consider the graph G′ obtained from G by adding a supersink t with a single outgoing edge ts and incoming edges
vt for all v ∈V . Then v ∈V is reachable from s in G iﬀs and v are strongly connected in G′. See also [vdBNS19].
3

## Page 4

dynamic #SSR in planar digraphs with �O(n4/5) update time; see Lemma 6.1 in Section 6. It is worth
noting that Voronoi diagrams-based techniques (as developed for distance oracles [GMWW18]) have
been used in the pairwise strong connectivity data structure [CK22]. However, as we discuss later
on, it is not clear how to apply those for the dynamic SCCs problem. This is why Theorem 1.1
relies on a completely diﬀerent path net approach developed in this paper.
Organization.
We review some standard planar graph tools in Section 2. Then, as a warm-up,
we show the data structure for dynamic SC in Section 3. In Section 4 we deﬁne the path net data
structure and show how it can be used to obtain a dynamic SCCs data structure. In Section 5 we
describe the path net data structure in detail. Finally, Section 6 is devoted to the fully dynamic
#SSR problem in planar digraphs.
#### 2
#### Preliminaries
In this paper we deal with directed graphs. We write V (G) and E(G) to denote the sets of vertices
and edges of G, respectively. We omit G when the graph in consideration is clear from the context.
A graph H is a subgraph of G, which we denote by H ⊆G, iﬀV (H) ⊆V (G) and E(H) ⊆E(G).
We write e = uv ∈E(G) when referring to edges of G. By GR we denote G with edges reversed.
A sequence of vertices P = v1 . . . vk, where k ≥1, is called an s →t path in G if s = v1,
vk = t and there is an edge vivi+1 in G for each i = 1, . . . , k −1. We sometimes view a path P
as a subgraph of G with vertices {v1, . . . , vk} and (possibly zero) edges {v1v2, . . . , vk−1vk}. For
convenience, we sometimes consider a single edge uv a path. If P1 is a u →v path and P2 is a
v →w path, we denote by P1 · P2 (or simply P1P2) a path obtained by concatenating P1 with P2.
A vertex t ∈V (G) is reachable from s ∈V (G) if there is an s →t path in G.
Planar graph toolbox.
An r-division [Fre87] R of a planar graph, for r ∈[1, n], is a decompo-
sition of the graph into a union of O(n/r) pieces P, each of size O(r) and with O(√r) boundary
vertices (denoted ∂P), i.e., vertices shared with some other piece of R. We denote by ∂R the set
�
P ∈R ∂P. If additionally G is plane-embedded, all pieces are connected, and the boundary vertices
of each piece P of the r-division R are distributed among O(1) faces of P that contain the vertices
from ∂P exclusively (also called holes of P), we call R an r-division with few holes.
[KMS13]
showed that an r-division with few holes of a triangulated graph can be computed in linear time.
Fully dynamic r-divisions.
Many dynamic algorithms for planar graphs maintain r-divisions
and useful piecewise auxiliary data structures under dynamic updates. Let us slightly generalize
the deﬁnition of an r-division with few holes to non-planar graphs by dropping the requirement
that G as a whole is planar but retaining all the other requirements (in particular, the individual
pieces are plane-embedded).
**Theorem 2.1. [CK22, KS98, Sub93] Let G = (V, E) be a planar graph that undergoes edge deletions**
and edge insertions (assumed to preserve the planarity of G). Let r ∈[1, n].
There is a data structure maintaining an r-division with few holes R of some G+, where G+
can be obtained from G by adding edges7, such that each piece P ∈R is accompanied with some
auxiliary data structures that can be constructed in T(r) time given P and use S(r) space.
The data structure uses O
�
n + n
r · S(r)
�
space and can be initialized in O
�
n + n
r · T(r)
�
time.
After each edge insertion/deletion, it can be updated in O(r + T(r)) worst-case time.
7Note that G+ need not be planar.
4

## Page 5

#### 3
#### Fully dynamic SC data structure
To illustrate the general approach and introduce some of the concepts used for obtaining Theo-
rem 1.1, in this section we ﬁrst prove Lemma 1.2. That is, we show that the information whether
a planar graph G is strongly connected can be maintained in �O(n2/3) time per update.
We build upon the following general template used previously for designing fully dynamic data
structures supporting reachability, strong connectivity, and shortest paths queries in planar graphs,
e.g., [Sub93, KS98, FR06, CK22, KMNS17]. As a base, we will maintain dynamically an r-division
with few holes R of G using Theorem 2.1 with auxiliary piecewise data structures to be ﬁxed later.
Intuitively, as long as the piecewise data structures are powerful enough to allow recomputing the
requested graph property (e.g., strong connectivity, shortest path between a ﬁxed source/target
pair) while spending r1−ǫ time per piece, for some choice of r we get a sublinear update bound
of �O(n/rǫ + r + T(r)). For example, if T(r) = O(r9.9) and ǫ = 0.1, for r = n0.1 we get �O(n0.99)
worst-case update time bound.
Reachability certiﬁcates.
[Sub93] described reachability certiﬁcates that sparsify reachability
between a subset of vertices lying on O(1) faces of a plane digraph G into a (non-necessarily planar)
digraph of size near-linear in the size of the subset in question. Formally, we have the following.
**Lemma 3.1 ([Sub93]). Let H be a plane digraph with a distinguished set ∂H ⊆V (H) lying on**
some O(1) faces of H. There exists a directed graph XH, where ∂H ⊆V (XH), of size �O(|∂H|)
satisfying the following property: for any u, v ∈∂H, a path u →v exists in H if and only if there
exists a u →v path in XH. The graph XH can be computed in �O(|H|) time.
**Remark 3.2. For Lemma 3.1 to hold, it is enough that ∂H lies on O(1) Jordan curves in the**
plane, each of them having the embedding of H entirely (but not strictly) on one side of the curve.
In particular, it is enough that ∂H lies on O(1) faces of some plane supergraph H′ with H ⊆H′.
Roughly speaking, [Sub93] uses reachability certiﬁcates as auxiliary data structures in Theo-
rem 2.1 in order to obtain a fully dynamic reachability data structure. Crucially, the union of the
piecewise certiﬁcates preserves pairwise reachability between the boundary vertices ∂R, or more
formally (see e.g. [CK22] for a proof):
**Lemma 3.3. For any u, v ∈∂R, u can reach v in G if and only if u can reach v in X = �**
P ∈R XP .
Strong connectivity data structure.
The union of certiﬁcates X preserves reachability, and
thus strong connectivity between the vertices ∂R := �
P ∈R ∂P.
As a result, if G is strongly
connected, then so is ∂R in X. But the reverse implication might not hold. It turns out that for
connected graphs, to have an equivalence, it is enough to additionally maintain, for each piece P,
whether P is strongly connected conditioned on whether ∂P is strongly connected in G.
In the following, we give a formal description of the data structure. As already said, the data
structure maintains a dynamic r-division R+ of a supergraph G+ of G (i.e., the input graph), as
given by Theorem 2.1. Since G ⊆G+, the pieces {P + ∩G : P + ∈R+} induce an r-division R of G;
however, a piece P ∈R is not necessarily connected and ∂P not necessarily lie on O(1) faces of P,
so R is not technically an r-division with few holes. Nevertheless, ∂P still lies on O(1) faces of a
connected plane supergraph P + of P that do not contain vertices outside ∂P. Consequently, by
Remark 3.2, we can still use Lemma 3.1 to construct a sparse reachability certiﬁcate for the piece
P ∈R. For obtaining Lemma 1.2, we do not require anything besides that, so for simplicity and
wlog. we can assume we work with R instead of R+.
5

## Page 6

While R evolves, each piece P is accompanied with a reachability certiﬁcate XP of Lemma 3.1.
Note that since |∂P| = O(√r), XP has size �O(√r) and can be constructed in �O(r) time. Moreover,
for each P, let C∂P be a directed simple cycle on the vertices ∂P. We additionally store the (1-bit)
information whether the graph P ∪C∂P is strongly connected. Clearly, this can be computed in
O(|P|) = O(r) time. All the accompanying data structures of a piece P ∈R can be thus constructed
in �O(r) time. Therefore, by Theorem 2.1, they are maintained in �O(r) time per update.
Finally, in a separate data structure, we maintain whether G is connected (in the undirected
sense). This can be maintained within no(1) worst-case update time deterministically even in general
graphs [GRST21]; in our case, also a less involved data structure such as [Fre85] would suﬃce.
After R and the accompanying data structures are updated, strong connectivity of G can be
veriﬁed as follows. First of all, the union X of all XP , P ∈R, is formed. Note that we can test
whether the vertices ∂R are strongly connected in X in O(|X|) = �O(n/√r) time by computing
the strongly connected components SX of X using any classical linear time algorithm. If G is not
connected, or ∂R is not strongly connected in X, we declare G not strongly connected. If, on the
other hand, ∂R is strongly connected in X, we simply check whether P ∪C∂P is strongly connected
for each P ∈R and if so, declare G strongly connected. This takes O(n/r) time. Thus, testing
strong connectivity takes �O(n/√r) time. The following lemma establishes the correctness.
**Lemma 3.4. G is strongly connected if and only if G is connected, the vertices ∂R are strongly**
connected in X, and for all P ∈R, P ∪C∂P is strongly connected.
Proof. First suppose that G is strongly connected. Then, G is clearly connected. Moreover, by
Lemma 3.3, ∂R is strongly connected in X. For contradiction, suppose that for some P ∈R and
u, v ∈V (P), u cannot reach v in P ∪C∂P . By strong connectivity of G, there exists some path
Q = u →v in G. Since u cannot reach v in P, Q is not fully contained in P. As a result, Q
can be expressed as Q1 · R · Q2, where Q1 = u →a, Q2 = b →v are fully contained in P, and
a, b ∈∂P. But there is a path Z = a →b in C∂P, so there is a u →v path Q1 · Z · Q2 in P ∪C∂P ,
a contradiction.
Now consider the “ ⇐= ” direction. Suppose G is connected, the vertices ∂R are strongly
connected in X, and for all P ∈R, P ∪C∂P is strongly connected. By Lemma 3.3, ∂R is strongly
connected in G. Consider any P ∈R and let x, y ∈V (P). We ﬁrst prove that there exists a path
x →y in G. Indeed, if an x →y path exists in P, it also exists in G. Otherwise, since P ∪C∂P is
strongly connected, there exists a path Q = x →y in P ∪C∂P that can be expressed as Q1 · R · Q2,
where Q1 = x →a and Q2 = b →y are fully contained in P and a, b ∈∂P. But since a, b ∈∂R,
by strong connectivity of ∂R, there exists a path R′ = a →b in G. Since Q1, Q2 ⊆G, Q1 · R′ · Q2
is an x →y path in G.
Now take arbitrary u, v ∈V (G). If there exists a piece in R containing both u and v, then we
have already proved that there exists a path u →v in G. Otherwise, let Pu, Pv, Pu̸ = Pv, be some
pieces of R containing u, v, respectively. We have Pu̸ = G and Pv̸ = G. Since G is connected, Pu
has at least one boundary vertex a ∈∂Pu. Similarly, Pv has at least one boundary vertex b ∈∂Pv.
We have proved that there exist paths u →a and b →v in G. But also a, b ∈∂R, so by the strong
connectivity of ∂R, there exists a path a →b in G as well. We conclude that there exists a path
u →v in G. Since u, v were arbitrary, G is indeed strongly connected.
The worst-case update time of the data structure is �O(r + n/√r) + no(1). By setting r = n2/3,
we obtain the following.
**Lemma 1.2. Let G be a planar digraph subject to planarity-preserving edge insertions and dele-**
tions. One can maintain whether G has a single SCC in �O(n2/3) worst-case time per update.
6

## Page 7

#### 4
#### Dynamic strongly connected components
The approach we take for maintaining strong connectivity in planar graphs does not easily generalize
even to dynamic SCCs counting. This is the case for the following reason. Even if the piece P is
ﬁxed (static), there can be possibly an exponential number of diﬀerent assignments of the vertices
∂P to the SCCs in G (when the other pieces are subject to changes), whereas for dynamic SC,
a non-trivial situation arises only when all of ∂P lies within a single SCC. In order to achieve
sublinear update time, for any assignment we need to be able to count the SCCs fully contained
in P in time sublinear in r after preprocessing P in only polynomial (and not exponential) time.
The following notion will be crucial for all our developments.
**Deﬁnition 4.1. Let P ∈R, and let A ⊆∂P. A path net ΠP (A) induced by A is the set of vertices**
of P that lie on some directed path in P connecting some two elements of A.
In other words, the path net ΠP (A) contains vertices v ∈V (P) such that v can reach A and
can be reached from A in P. We call a path net ΠP (A) closed if A = ΠP(A) ∩∂P, that is, there
are no boundary vertices of P outside A that can reach and can be reached from A.
The following key lemma relates a piece’s path net to the SCCs of G.
Lemma 4.2. Let S be an SCC of G containing at least one boundary vertex of P, i.e., S ∩∂P̸ = ∅.
Then the path net ΠP (S ∩∂P) is closed and equals S ∩V (P).
Proof. Let us ﬁrst argue that ΠP (S ∩∂P) is closed. If it was not, there would exist b ∈∂P \ S
such that there exist paths b →(S ∩∂P) and (S ∩∂P) →b in P. It follows that b can reach and
be reached from S in G, i.e., b is strongly connected with S. Hence, b ∈S, a contradiction.
Let v ∈ΠP (S ∩∂P). Since v can reach and can be reached from S ∩∂P in P, then it is indeed
strongly connected with S in G, since the vertices S are strongly connected in G. So v ∈S ∩V (P).
Now let v ∈S ∩V (P). Pick any b ∈S ∩∂P (possibly b = v if v ∈∂P). There exists paths
R = v →b and Q = b →v in G. Note that R has some preﬁx R1 = v →a that is fully contained
in P and a ∈∂P. Similarly, Q has a suﬃx Q1 = c →v that is fully contained in P and c ∈∂P.
Since there exists paths v →a, a →b, b →c, c →v in G, vertices a, b, c are strongly connected
in G. So a, c ∈S ∩∂P. The paths R1, Q1 certify that v can be reached from and can reach S ∩∂P
in P. Therefore, v ∈ΠP(S ∩∂P) as desired.
If an SCC S is as in Lemma 4.2, then since the vertices ∂P might be shared with other pieces
of R, ΠP(S ∩∂P) \ ∂P constitutes the vertices of S contained exclusively in the piece P. As there
are only �O(n/√r) boundary vertices through all pieces, their aﬃliation to the SCCs of G can be
derived from the (SCCs of the) certiﬁcate graph X = �
P ∈R XP (deﬁned and maintained as in
Section 3), i.e., they may be handled eﬃciently separately. Consequently, being able to eﬃciently
aggregate labels – or report the elements – of the sets of the form ΠP (A) \ ∂P (where ΠP (A) is
closed) is the key to obtaining an eﬃcient implicit representation of the SCCs of G. Our main
technical contribution (Theorem 4.3) is the path net data structure enabling precisely that. The
data structure requires a rather large �O(r3) preprocessing time but achieves the goal by supporting
queries about A ⊆∂P in near-optimal �O(|A|) time. Formally, we show:
**Theorem 4.3. Let P ∈R and let α : V (P) →R be a weight function. In �O(r3) time one can**
construct a data structure satisfying the following.
Given a subset A ⊆∂P such that ΠP (A) is closed, in �O(|A|) time one can:
• create an iterator that enables listing elements of ΠP(A) \ ∂P in O(1) time per element,
• aggregate weights over ΠP (A) \ ∂P, i.e., compute �
v∈ΠP (A)\∂P α(v).
7

## Page 8

**Remark 4.4. We do not require using subtractions to compute the aggregate weights. In fact,**
the data structure of Theorem 4.3 can be easily modiﬁed to aggregate weights coming from any
semigroup, e.g., one can compute the max/min weight in ΠP(A) \ ∂P within these bounds.
Our high-level strategy is to maintain the certiﬁcates and path net data structures accompanying
individual pieces along with the r-division. Roughly speaking, to obtain the information about the
SCCs of G beyond how the partition of ∂R into SCCs looks like, we will query the path net data
structures for each piece P with the sets A equal to the SCCs of X having non-empty intersection
with ∂P. We prove Theorem 4.3 later on, in Section 5.
In the remaining part of the section, we explain in detail how, equipped with Theorem 4.3, a
dynamic (implicit) strongly connected components data structure can be obtained. As in Section 3,
we maintain an r-division R dynamically, and maintain sparse reachability certiﬁcates XP along
with the set SX of SCCs of X = �
P ∈R XP . Moreover, for each P we store the strongly connected
components SP of P. Let S∂P be the elements of SP that contain a boundary vertex, and SP \∂P
the elements of SP that do not. Clearly, we have SP = S∂P ∪SP \∂P and (�SP) ∩
��SP \∂P
�
= ∅.
For each piece P ∈R, we additionally store a path net data structure DP of Theorem 4.3 with
an appropriately deﬁned weight function (to be chosen depending on the application later). Note
that for a piece P, all the auxiliary data structures accompanying P that we have deﬁned can be
computed in �O(r3) time. We now consider the speciﬁc goals that can be achieved this way.
Finding the largest SCC.
Denote by S∗the largest SCC of G. To be able to identify S∗, and
e.g., compute its size, we proceed as follows. For each piece P, we additionally maintain the largest
SCC S∗
P of P. The sizes of all the SCCs of P, in particular the size of S∗
P, can be easily found and
stored after computing SP .
Note that if the largest SCC S∗of G is not contained entirely in any individual piece P (and
thus is larger than maxP ∈R |S∗
P |), it has to intersect ∂R. More speciﬁcally, in this case for each
piece P such that S∗∩V (P)̸ = ∅, we have S∗∩∂P̸ = ∅.
Recall that by Lemma 3.3, X = �
P ∈R XP preserves the strong connectivity relation on the
vertices ∂R. Therefore, if S∗intersects ∂R, it has to contain B ∩∂R for some SCC B of X. For
any such B, we can compute the size of the SCC SB of G satisfying B ∩∂R ⊆SB as follows. First
of all, |SB ∩∂R| = |B ∩∂R| since B is an SCC of X. It is thus enough to compute, for all P ∈R,
|SB ∩(V (P) \ ∂P)|. Since the sets V (P) \ ∂P are pairwise disjoint across the pieces, by adding
these values, we will get the desired size |SB|.
We have already argued that if B ∩∂P = ∅, then SB ∩V (P) = ∅. If, on the other hand, B ∩∂P
is non-empty, by Lemma 4.2, if we use the weight function α(v) ≡1 in the piecewise data structures
DP of Theorem 4.3, we can compute |SB ∩(V (P) \ ∂P)| = �
v∈ΠP (B∩∂P )\∂P α(v) in �O(|B ∩∂P|)
time using the input set A := B ∩∂P. We conclude that the sizes SB for all B ∈SX can be
computed in time
�O




�
B∈SX
�
P ∈R
B∩∂P̸ =∅
|B ∩∂P|



= �O




�
P ∈R
�
B∈SX
B∩∂P̸ =∅
|B ∩∂P|



= �O
��
P ∈R
|∂P|
�
= �O(n/√r).
(1)
Finally, S∗is either equal to the largest SB for B ∈SX, or the largest S∗
P (through P ∈R). The
latter is the case if maxB∈SX |SB| < maxP ∈R |S∗
P|. Which case we fall into is easily decided once
all the O(n/√r) sizes |SB| are computed.
8

## Page 9

Accessing the SCC of a speciﬁed vertex.
Suppose ﬁrst that we know the SCC Sv of G
containing a query vertex v, and additionally whether Sv intersects ∂R. If Sv ∩∂R = ∅, then v is
a vertex of a unique piece P, and Sv ∈SP \∂P . In this case, we can clearly compute the size of Sv
and report the elements of Sv in O(1) time since Sv ∈SP is stored explicitly.
Otherwise, if Sv∩∂R̸ = ∅, we reuse the information that we have computed for ﬁnding the largest
SCC. We have already described how to compute the sizes of all the SCCs S of G intersecting ∂R (in
particular Sv) along with these respective intersections in �O(n/√r) time upon update. Moreover,
for all P ∈R we have computed |S∩(V (P)\∂P)| using the data structure DP of Theorem 4.3. As a
result, we can store, for each such S, a subset L(S) ⊆R of pieces P such that S ∩(V (P)\∂P)̸ = ∅.
Recall that for all P ∈L(S), we can also use DP to create an iterator for reporting the elements of
S ∩(V (P)\∂P) in O(1) time per element. So, in order to eﬃciently report elements of any such S,
we ﬁrst report the vertices of S ∩∂R, and then the elements of each S ∩(V (P)\∂P) for subsequent
pieces P ∈L(S). Indeed, one needs only O(1) worst-case time to ﬁnd each subsequent vertex of S.
Finally, we are left with the task of of ﬁnding the SCC Sv of a query vertex v ∈V . It is
not clear how to leverage path net data structures for that in the case when Sv intersects ∂R.
Instead, we use the data structure of [CK22] in a black-box way. That data structure handles fully
dynamic edge updates in �O(n4/5) worst-case time, and provides O(log2 n) worst-case time access
to consistent (for queries issued between any two subsequent updates) SCC identiﬁers of individual
vertices8. Using [CK22], after every update we ﬁnd the identiﬁers I of the SCCs of vertices ∂R in
G in �O(n/√r) time. Now, to ﬁnd the SCC of v upon query, we ﬁnd the identiﬁer iv of the SCC
containing v in O(log2 n) time. If iv ∈I (which can be tested in O(log n) time), we obtain that v
is in an SCC of G intersecting ∂R and some vertex bv from the intersection. bv can be in turn used
to access L(Sv) and thus enable reporting the elements of Sv. Otherwise, if iv /∈I, S ∩∂R = ∅and
thus S equals the unique SCC from SP \∂P containing v in the unique piece P containing v.
Counting strongly connected components.
Let us separately count SCCs S∂R that intersect
∂R and those that do not. The former can be counted in �O(n/√r) time by counting the SCCs of
X that intersect ∂R (that we maintain). The latter can be computed as follows. Consider the sum
Φ = �
P ∈R |SP \∂P |. If we wanted the sum Φ to count the SCCs not intersecting ∂R, then an SCC
S ∈SP \∂P contributes to the sum unnecessarily precisely when S is not an SCC of G. To see that,
note that if an SCC S of P is not an SCC of G, it has to be a part of another SCC S′ of G that
also contains vertices of other pieces, i.e., S′ intersects ∂R. From Lemma 4.2, we conclude:
**Corollary 4.5. An SCC S ∈SP \∂P is not an SCC of G iﬀthere exists (precisely one) SCC B**
of X such that S ⊆ΠP (B ∩∂P) (or equivalently, such that S ∩ΠP (B ∩∂P)̸ = ∅).
As a result, we can count the number of SCCs in G that do not intersect ∂R by subtracting
from Φ, for each P ∈R, and each B ∈SX the number cP,B of SCCs in SP \∂P that intersect
ΠP (B ∩∂P). To this end, we can use the data structure DP of Theorem 4.3 built upon P (and
maintained as described before) with a weight function α on V (P) assigning 1 to an arbitrary
single vertex vS of each SCC S ∈SP \∂P , and 0 to all other vertices. By Corollary 4.5, with such
a weight function, cP,B = �
v∈ΠP (B∩∂P )\∂P α(v) can be computed in �O(|B ∩∂P|) time using DP .
Consequently, similarly as in (1), over all B ∈SX, and P ∈R, computing all the values cP,B will
take �O(n/√r) time. As mentioned before, the SCC count is obtained by subtracting those from Φ
and adding the result to the count of S∂R.
8The query time of that data structure can be easily reduced to O(log n · log log n) without aﬀecting the �O(n4/5)
update bound if one simply replaces the classical MSSP data structure [Kle05] used internally for performing point
location queries in additively weighted Voronoi diagrams [GMWW18] with the MSSP data structure of [LP21].
9

## Page 10

Depending on the application, the worst-case update time of the data structure is �O(n/√r+r3)
or �O(n/√r + r3 + n4/5). The bound is optimized for r = n2/7 and this yields the following.
**Theorem 1.1. Let G be a planar digraph subject to planarity-preserving edge insertions and dele-**
tions. There exists a data structure maintaining the strongly connected components of G implicitly
in �O(n6/7) worst-case time per update. Speciﬁcally:
• The data structure maintains the number of SCCs and the size of the largest SCC in G.
• For any query vertex v, in O(log2 n) time the data structure can compute the size of the SCC
of v, and enable reporting the elements of the SCC of v in O(1) worst-case time per element.
#### 5
#### The path net data structure
This section is devoted to describing the below key component of our dynamic SCCs data structure.
**Theorem 4.3. Let P ∈R and let α : V (P) →R be a weight function. In �O(r3) time one can**
construct a data structure satisfying the following.
Given a subset A ⊆∂P such that ΠP (A) is closed, in �O(|A|) time one can:
• create an iterator that enables listing elements of ΠP(A) \ ∂P in O(1) time per element,
• aggregate weights over ΠP (A) \ ∂P, i.e., compute �
v∈ΠP (A)\∂P α(v).
**5.1**
**Overview**
[CK22] showed that for any SCC S of G, V (P) ∩S forms an intersection of two cells coming from
two carefully prepared additively weighted Voronoi diagrams on P with sites ∂P. As a result, they
could use Voronoi diagram point location mechanism [GMWW18, LP21] for testing in O(polylog n)
time whether a query vertex lies in such an intersection. If we tried to follow this approach, we
would need to be able to aggregate/report vertices in such intersections of cells coming from two
seemingly unrelated Voronoi diagrams. This is very diﬀerent from just testing membership, and it
is not clear whether this can be done eﬃciently.
Instead, in order to prove Theorem 4.3, we take a more direct approach. As is done typically,
we ﬁrst consider the situation when A lies on a single face of P. In the single-hole case, the ﬁrst
step is to reduce to the case when the input piece P is acyclic; note that if a vertex lies in the
path net ΠP(A), its entire SCC in P does. Acyclicity and appropriate perturbation [EFL18] allows
us to pick a collection of paths πu,v, for all u, v ∈∂P, such that every two paths in the collection
are either disjoint or their intersection forms a single subpath of both. This property makes the
paths πu,v particularly convenient to use for cutting the piece P into smaller non-overlapping parts.
More speciﬁcally, the paths πu,v are used to partition – using a polygon triangulation-like
procedure – a queried net ΠP (A) into regions in the plane with vertices B ⊆A bounded by either
fragments of the face of P containing ∂P or some paths πu,v for u, v ∈B (so-called base instances).
A base instance has a very special structure guaranteeing that for a given vertex v ∈V (P) \ ∂P,
there are only O(1) pairs s, t ∈B such that an s →v →t path exists in P. At the end, this
crucial property can be used to reduce a base instance query B even further to looking up �O(|B|)
preprocessed answers for base instances with at most 5 vertices from ∂P, of which there are at
most �O(|∂P|5) = �O(r5/2). The precomputation of small base instances can be done in �O(r3) time.
For eﬃciently implementing the polygon triangulation-like partition procedure – which repeat-
edly cuts oﬀbase instances from the “core” part of the problem – we develop a dynamic data
10

## Page 11

structure for existential reachability queries on a single face of a plane digraph (Lemma 5.3, proved
in Section 5.8). To this end, we leverage the single-face reachability characterization of [IKŁS17].
As the ﬁnal step, we show a reduction from the case when A can lie on k faces on P to the case
when A lies on k −1 faces. The reduction – which eventually reduces the problem to the single-hole
case – can blow up the piece’s size by a constant factor. However, since there are only O(1) holes
initially, the general case can still be solved only a constant factor slower than the single-hole case.
**5.2**
**Reducing to the acyclic case**
Recall that P is a piece of an r-division with few holes R and thus has size O(r). Moreover, ∂P lies
on O(1) faces (holes) of some supergraph P + of P and |∂P| = O(√r). For simplicity, we will not
diﬀerentiate between the faces/holes of P and P +. Whenever we refer to a hole h of P, we mean a
closed curve h in the plane such that whole embedding of P lies weakly on a single side of h, and
only vertices ∂P may lie on the curve h.
First of all, we compute the strongly connected components SP of P. Observe that from the
point of view of supported queries, all vertices of a single SCC S ∈SP are treated exactly the same:
when a single vertex v ∈S \∂P is reported (or its weight α(v) is aggregated), all other vertices from
S \ ∂P are as well. For each S ∈SP we precompute the aggregate weight α(S) = �
v∈S\∂P α(v) in
O(r) time. We then contract each strongly connected component S ∈SP into a single vertex vS.
Crucially, since each subgraph P[S] is connected in the undirected sense, contractions can be
performed in an embedding preserving way (via a sequence of single-edge contractions), so that:
• The obtained graph P ′ is acyclic.
• The vertices ∂P ′ := {vS : S ∈SP , S ∩∂P̸ = ∅} lie on O(1) faces of (a supergraph of) P ′.
Indeed, to see the latter property, label each b ∈∂P initially each with hole that b lies on and make
non-boundary vertices unlabeled. When the vertices merge, label the resulting vertex using one of
the involved vertices’ labels, if any of them has one. At the end there will be still O(1) labels, each
vertex of ∂P ′ will have one of these labels, and for each label, all the vertices holding that label
will be incident to a single face of P ′. Clearly, |P ′| = O(r) and |∂P ′| = O(√r).
**Lemma 5.1. Suppose a data structure D′ of Theorem 4.3 is built for the acyclic graph P ′ with the**
weight function α′(vS) := α(S) = �
v∈S\∂P α(v). Then, a query A ⊆∂P from Theorem 4.3 can be
reduced, in O(|A|) time, to a query about A′ = {vS : S ∈SP , S ∩A̸ = ∅} issued to D′.
Proof. By the assumption that ΠP (A) is closed, we have that ΠP (A) contains only such S ∈SP
that S∩∂P ⊆A. If the set ΠP ′(A′) contained some vR ∈∂P ′\A′, then in the graph P a vertex from
R∩(∂P \A) could reach and could be reached from A, which would contradict ΠP (A)∩∂P = A. As
a result, A′ is indeed a valid query parameter to the data structure D′ and in �O(|A′|) ≤�O(|A|) time
we can gain reporting access to ΠP ′(A′) \ ∂P ′ or aggregate the weights of ΠP ′(A′) \ ∂P ′. Observe
that any vertex vS ∈ΠP ′(A′)\∂P ′ corresponds to a subset S ⊆ΠP (A)\∂P. These subsets S, being
strongly connected components of P, are clearly pairwise disjoint. So the reporting procedure, when
D′ reports vS, can simply report the individual vertices of S one by one. Moreover, the weight
α(vS) equals the aggregate weight �
v∈S α(v). It is easy to see that this way, using D′ we can
actually eﬃciently report/aggregate all the vertices of (ΠP (A)\∂P)∩(�{S : vS ∈ΠP ′(A′) \ ∂P ′}),
or, in other words, the vertices of ΠP (A)\∂P that are not strongly connected to a boundary vertex
of P. However, some vertices from ΠP (A) \ ∂P are not necessarily in �{S : vS ∈ΠP ′(A′) \ ∂P ′}.
But these are precisely the non-boundary vertices of P that are strongly connected to some vertex
of A in P. As a result, we can handle these remaining vertices by iterating over the O(|A|) SCCs
of P that intersect A.
11

## Page 12

In the following we will assume that P is an acyclic graph. We will no longer need the assumption
ΠP (A)∩∂P = A; this was only needed for the eﬃcient reduction to the acyclic case. Consequently,
we will design a data structure with query time �O(|A|) even if A ⊊ΠP (A) ∩∂P.
In the remaining part of this section, we assume we only want to handle queries where the query
set A lies on a single hole h of an acyclic piece P. We present the reduction of the general case to
the single-hole case in Section 5.7. Our strategy for the single-hole case will be to eﬃciently break
the problem into subproblems for which we have the answer precomputed.
**5.3**
Picking non-crossing paths.
We ﬁrst ﬁx, for any u, v ∈V (P) such that u can reach v, one particular u →v path πu,v ⊆P. We
apply the perturbation scheme of [EFL18] to P, so that the shortest paths in P become unique.
For any u, v ∈V (P) such that u can reach v in P, we deﬁne πu,v to be the unique shortest u →v
path in P. Note that each πu,v is a simple path in P. We have the following crucial property.
Lemma 5.2. Let u, v, x, y ∈V (P) be such that u can reach v and x can reach y in P.
If
V (πu,v) ∩V (πx,y)̸ = ∅, then πu,v and πx,y share a single (possibly zero-edge) subpath.
Proof. Let a (b) be the ﬁrst (last, resp.) vertex on πu,v that is also a vertex of πx,y. πu,v can
be expressed as Q1 · T · Q2, where T = a →b. Moreover, V (πu,v) ∩V (πx,y) ⊆V (T). If a̸ = b,
the vertex b cannot appear before a on πx,y, because then a and b would lie on a cycle in P,
contradicting acyclicity of P. As a result, πx,y has an a →b subpath as well. Since shortest paths
in P are unique and shortest paths have optimal substructure, the a →b subpath of πx,y equals T.
So, πx,y can be expressed as R1 · T · R2. Since πx,y is simple, and V (πu,v) ∩V (πx,y) ⊆V (T), we
indeed have πu,v ∩πx,y = T.
Observe that since P is a DAG, for u, v ∈V (P), u̸ = v, πu,v and πv,u cannot both exist. When
one of them exists, we will sometimes write π{u,v} to denote the one that exists.
**5.4**
**Generalization**
Before we proceed, we need to state our problem in a more general way that will enable decompo-
sition into smaller subproblems of similar kind. Let us ﬁrst ﬁx a counterclockwise order of V (h),
as follows. Let u1, e1, u2, e2, . . . , ur, er be the sequence of vertices and edges on a counterclockwise
bounding walk of h with an arbitrary starting point. The encountered vertices ui might not be all
distinct since h can be a non-simple face in general. The order ≺h of V (h) that we use is obtained
by removing duplicate vertices from the sequence in an arbitrary way, i.e., for each v ∈V (h) we
pick one index iv such that uiv = v. If x, y ∈V (h) and ix < iy, then we deﬁne Cx,y to be the curve
eixeix+1 . . . eiy−1. Otherwise, if ix > iy, then Cx,y = eixeix+1 . . . ere1e2 . . . eiy−1. If h is simple, then
Cx,y is a simple curve. However, in general, Cx,y can be self-touching but it does not cross itself.
Suppose B ⊆∂P ∩V (h) is given ordered by ≺h. Moreover, for each pair of neighboring (i.e.,
appearing consecutively in the cyclic order of B given by ≺h) vertices x, y of B, a curve Φx,y
connecting x to y is given. The curve Φx,y equals either π{x,y} or Cx,y. Let Φ be the closed curve
formed by concatenating the subsequent curves Φx,y for all neighboring x, y ∈B. For brevity,
we also extend the notation Φa,b to non-neighboring vertices a, b of B, and deﬁne Φa,b to be a
concatenation of the curves Φx,y for all neighboring pairs (x, y) between a and b on Φ. We don’t
require Φ to be a simple (Jordan) curve; parts of it may be overlapping. Whereas Φ is allowed to
be self-touching, it does not cross itself, like e.g., the cycle bounding a non-simple face of a plane
graph. Let P[Φ] denote the region of P that lies weakly inside the curve Φ.
12

## Page 13

The objective of the problem (B, Φ) is to aggregate weights of (or report) the vertices of
ΠP (B) \ ∂P that lie strictly inside Φ. More formally, we want to aggregate vertices v that lie,
at the same time, strictly on the left side of each of the curves Φx,y (seen as a curve directed from
x to y) where x, y are neighboring elements of B sorted by ≺h.9 Note that with such a deﬁned
problem, the original goal of the query procedure can be rephrased as (A, h) since all the vertices
of ΠP(A) \ ∂P indeed lie strictly inside h.
**5.5**
**Preprocessing**
Preprocessing for small instances and subproblems.
• For any tuple B = (b1, . . . , bq) of at most 4 vertices of ∂P appearing in that order in ≺h, and
any out of at most 2q = O(1) possible curves Φ that might constitute the problem (B, Φ),
we precompute the aggregate weight and the list of vertices in ΠP(B) \ ∂P that lie strictly
inside Φ. This can clearly be done in �O(|∂P|4 · |P|) = �O(r3) time.
• For any 5-tuple τ = (b0, . . . , b4) ordered by ≺h, and any out of at most 24 possible curves
Φbi,bi+1 ∈{π{bi,bi+1}, Cbi,bi+1}, where i ∈{0, . . . , 3}, we precompute and store the set Xτ of
vertices x ∈V (P) \ ∂P such that:
1. x lies on some path connecting b1 and b2 in P,
2. x does not lie on any path connecting b0 and b1 in P,
3. x lies strictly to the left of each Φbi,bi+1 for i = {0, . . . , 3}.
We also store the aggregate weight w(Xτ). This preprocessing can be performed in a brute-
force way in �O(|∂P|5 · |P|) = �O(r7/2) time. It can be also optimized fairly easily to �O(r3)
time and space, as follows.
First, for every a ∈∂P, and v ∈V (P) \ ∂P, ﬁnd the earliest vertex za,v ∈∂P following a in
the order ≺h such that v does not lie strictly to the left of π{a,za,v}. Note that having ﬁxed
a ∈∂P, the property of v being strictly left of π{a,b} is monotonous in the vertex b ∈∂P
following a. The vertices za,v can be computed in �O(|∂P|2 · |P|2) = �O(r3) naively.
Having ﬁxed (b0, . . . , b3), compute the set X′ of all vertices x ∈V (P) \ ∂P satisfying all the
above conditions possibly except the one that x lies strictly to the left of Φb3,b4. Computing all
such X′ takes �O(|∂P|4·|P|) = �O(r3) time. Now, for each of the �O(r2) obtained sets X′, in �O(r)
time we sort the elements x ∈X′ by the value zb3,x where zb3,x (b3 ≺h zb3,x) appearing later
in ≺h is considered smaller. This way, for each possible b4 ∈B, the desired set of vertices Xτ
forms a preﬁx of the vertices X′: we have x ∈Xτ iﬀx ∈X′ and zb3,x appears later than b4
(and after b3) in the order ≺h. Storing X′ sorted like that, along with the aggregate preﬁx
weights, allows us to aggregate/report any set Xτ for a 5-tuple τ = (b0, . . . , b4) and 4-tuple
(Φbi,bi+1)3
i=0 in O(1) time after only �O(r3) preprocessing.
• For any u, v ∈∂P, we store the path π{u,v} itself, along with aggregate weights of all its
subpaths. This data can be computed in �O(|∂P|2 · |P|2) = �O(r3) time in a brute-force way.
9Even more formally, assuming P is embedded in such a way that h is the inﬁnite face of a supergraph of P, we
are interested in the vertices lying in the intersection of the regions strictly inside closed curves Φx,y · Cy,x for all
neighboring x, y in B.
13

## Page 14

• Finally, for any two pairs (u, v), (x, y) ∈∂P × ∂P, we compute the intersection of the paths
π{u,v} and π{x,y}. By Lemma 5.2, that intersection is either empty or is a subpath of both
these paths. Hence, it is enough to store the two endpoints of the intersection subpath only.
The desired intersections can be found in �O(|∂P|4 · |P|) = �O(r3) time in a brute-force way.
Existential reachability data structure.
We also build data structures L, LR of the following
lemma for P and P R, respectively.
**Lemma 5.3. In �O(r) time one can construct a data structure maintaining an (initially empty) set**
Z ⊆∂P ∩V (h) and supporting the following operations in O(polylog n) time:
• insert or delete a single b ∈∂P ∩V (h) either to or from Z.
• for any query vertex v ∈(∂P ∩V (h)) \ Z, ﬁnd any z ∈Z (if exists) that v can reach in P.
The proof of Lemma 5.3 is deferred to Section 5.8.
**5.6**
**Answering queries**
We now proceed with the description of our algorithm solving the general problem (B, Φ).
Base case.
Let the elements of B = {b1, . . . , bk} be sorted according to their order ≺h on Φ. For
convenience, identify bk+l with bl for any integer l.
We ﬁrst consider the easier base case, with the following additional requirement:
For any 1 ≤i < j ≤k, if bi can reach bj or can be reached from bj in P, then either
j = i + 1 or (i, j) = (1, k).
If k ≤4, we will simply return the precomputed aggregate weight, or an iterator to a list of
vertices in ΠP (B) \ ∂P strictly inside Φ. So suppose k ≥5. We start with the following lemma.
**Lemma 5.4. Let v ∈ΠP (B) \ ∂P lie strictly inside Φ. Then:**
• There exists such i that v lies on some bi →bi+1 or on some bi+1 →bi path in P.
• Moreover, there is at most one more pair {x, y} ⊆B, {x, y}̸ = {bi, bi+1} such that v lies on
some x →y or y →x path in P, and either {x, y} = {bi−1, bi}, or {x, y} = {bi+1, bi+2}.
Proof. Item (1) follows easily by the additional requirement of the base case. Let v lie on some
bj →c path in P, where c ∈B. Since P is acyclic, we have that bj̸ = c and thus c ∈{bj−1, bj+1}.
If c = bj+1, we put i = j and if c = bj−1, we put i = j −1.
For item (2), consider the case when v lies on some bi →bi+1; the case when v lies on a
bi+1 →bi path is symmetric. Suppose v also lies on some x →y path in P, where x, y ∈B, x̸ = y,
{x, y}̸ = {bi, bi+1}. Since bi can reach y through v, y ∈{bi−1, bi+1} by the requirement. Similarly,
since x can reach bi+1 through v, x ∈{bi, bi+2}. We cannot have x = bi+2 and y = bi−1 since
bi+2 reaching bi−1 is a contradiction with the ﬁrst base case requirement for k ≥5. As a result,
(x, y)̸ = (bi, bi+1) implies (x, y) = (bi, bi−1) or (x, y) = (bi+2, bi+1). Moreover, v cannot lie on both
some bi →bi−1 path and some bi+2 →bi+1 path, since then bi+2 could reach bi−1, which is again a
contradiction for k ≥5.
14

## Page 15

By Lemma 5.4, each v ∈ΠP (B) \ ∂P falls into exactly one of the k sets Yi, for i = 1, . . . , k,
such that Yi contains those v in V (P) \ ∂P that lie on a path in P connecting bi and bi+1 (in
any direction), but at the same time do not lie on any path connecting bi−1 and bi in P (in any
direction). Indeed, if v appears only on paths connecting bi and bi+1, it will be included in Yi. On
the other hand, if v appears both on paths connecting bi and bi+1 and on paths connecting bi+1
and bi+2, it will be included only in Yi, but not in Yi+1.
**Lemma 5.5. Suppose v ∈Yi. Then v lies strictly inside Φ if and only if v lies strictly on the left**
side of Φbi−1,bi, Φbi,bi+1, Φbi+1,bi+2, and Φbi+2,bi+3.
Proof. Since strictly inside Φ means strictly to the left of all Φbj,bj+1, the “ =⇒” direction is trivial.
Consider the “ ⇐= ” direction. For contradiction, suppose v does not lie strictly inside Φ.
Then, for some j /∈{i −1, i, i + 1, i + 2}, v lies weakly to the right of Φbj,bj+1. Since v ∈V (P) \ ∂P
and the hole h contains only vertices of ∂P, this means that Φbj,bj+1 = π{bj,bj+1}. Since bj and bj+1
are consecutive in B, and i /∈{j, j + 1}, bi lies weakly to the left of π{bj,bj+1}.
By v ∈Yi, the vertex v lies on a path Q connecting bi and bi+1 in P. Since v and bi lie weakly
on diﬀerent sides of π{bj,bj+1}, the path Q has to cross π{bj,bj+1} at a vertex w appearing not later
than v on Q (possibly v = w). If Q = bi →bi+1, the existence of w implies that there exists an
s →bi+1 path in P going through v such that s ∈{bj, bj+1}. By v ∈Yi, this implies s ∈{bi, bi+2}.
As a result, j ∈{i −1, i, i + 1, i + 2}, a contradiction. Similarly, if Q = bi+1 →bi, there exists an
s →bi path in P going through v such that s ∈{bj, bj+1}. But on the other hand by v ∈Yi we
have s = bi+1 so j ∈{i, i + 1}, a contradiction.
As a result, we can equivalently aggregate vertices v in each Yi under a (seemingly) weaker
requirement that v lies strictly on the left side of Φbi−1,bi, Φbi,bi+1, Φbi+1,bi+2, and Φbi+2,bi+3. But
this is, again, part of the precomputed data for the tuple (bi−1, bi, bi+1, bi+2, bi+3).
Consequently, there are k disjoint sets Yi to consider. We can thus aggregate weights or construct
a list for reporting vertices from v ∈ΠP (B) \ ∂P strictly inside Φ in O(k) time. We thus obtain:
Lemma 5.6. The base case can be handled in O(|B|) time.
General case.
To solve the general case, we reduce it to a number of base case instances. To this
end, we maintain a partition of B = S ∪T such that S precedes T on Φ. Let S = {s1, . . . , sp} and
T = {t1, . . . , tq}. We will gradually simplify the problem while maintaining the following invariants:
(1) For any u, v ∈B, if u can reach v in P, then πu,v ⊆P[Φ].
(2) For any 1 ≤i < j ≤p, if si can reach sj or can be reached from sj, then j = i + 1.
(3) If x, y ∈B are neighbors in the counterclockwise order ≺h on Φ and Φx,y = π{x,y}, then
x, y ∈S.
(4) In the data structures L, LR of Lemma 5.3, the set Z satisﬁes Z = S \ {sp}.
The algorithm will gradually modify B, S, T, Φ until we have S = B and T = ∅. Note that when
T = ∅, (B, Φ) = (S, Φ) satisﬁes the requirement of the base case and can be solved in �O(|B|) time.
Initially we put Φ = h, S = {b1, b2}, and insert b1 to Z to satisfy the invariants.
The main loop of the procedure runs while T̸ = ∅and does the following. Using L and LR, in
O(polylog n) time we test whether t1 can reach Z or can be reached from Z in P. If this is not the
case, we simply move t1 to the end of S, an update Z accordingly. Note that |T| decreases then.
15

## Page 16

#### Otherwise, we can ﬁnd all vertices X = {x1, . . . , xl} ⊆Z that t1 can reach or can be reached
#### from in �O(|X|) by repeatedly extracting them from the data structures L, LR. Additionally we sort
X so that the order x1, . . . , xl matches the order of S on Φ. Let πi denote the path π{t1,xi} possibly
reversed to go from t1 to xi, and πR
#### i denote the reverse πi going from xi to t1. The vertices X are
used to “cut oﬀ” l base case instances, as follows. For i = 0, . . . , l, let Si denote the vertices of
S between xi and xi+1 on Φ (inclusive), where we set xl+1 := sp, x0 := s1. We split the problem
#### (B, Φ) into the following subproblems (see Figure 1 for better understanding):
1. For each i = 1, . . . , l −1, an instance (Si ∪{t1}, Φxi,xi+1 · πR
i+1 · πi).
2. An instance (Sl ∪{t1}, Φxl,t1 · πl).
3. An instance (S0 ∪T, Φs1,x1 · πR
1 · Φt1,s1).
s1
s2
x1 = sg
x2
x3
x4
sp
t1
t2
tq
π1 = πt1,x1
π2 = πt1,x2
π3 = πt1,x3
π4
#### Figure 1: Splitting the instance (B, Φ), where B = S ∪T, into 5 smaller instances with paths
π1, . . . , πl (either originating or ending in t1) for l = 4. The vertices S = {s1, . . . , sp} are shown in
blue, whereas the vertices T = {t1, . . . , tq} in red. The black arrows and dashed lines represent the
#### individual parts of the curve Φ: paths of the form πu,v or parts of the curve h, respectively. Note
that the black arrows appear only on the Φs1,sp part of Φ. The vertices x1, . . . , x4, marked green,
#### are precisely all the vertices of S \ {sp} that t1 can reach or can be reached from. The obtained
#### smaller instances are marked with distinct patterns. The instances marked with line patterns (types
#### 1 or 2) are base instances. The instance marked using a dotted pattern (type 3) might constitute
#### the only obtained instance that is not a base instance (for which the algorithm continues).
#### Lemma 5.7. For each of the above subproblems (B′, Φ′), and u, v ∈B′, if u can reach v in P, then
πu,v ⊆P[Φ′].
Proof. Note that (B′, Φ′) is obtained from (B, Φ) by cutting it out of (B, Φ) with at most two paths
π{t1,a}, π{t1,b}, for some t1, a, b ∈B′ ⊆B. By our assumption, πu,v ⊆P[Φ]. As a result, if πu,v
#### 16

## Page 17

was not contained in P[Φ′], then πu,v would need to cross either π{t1,a} or π{t1,b}. However, this is
impossible by Lemma 5.2 and since u, v ∈V (P[Φ′]).
Lemma 5.8. The obtained instances of types 1 and 2 above fall into the base case.
Proof. To see that the base case requirement is satisﬁed, recall that by the invariant posed on S, if
two elements of Si, where i ∈{1, . . . , l}, are related (wrt. reachability in P), they are neighboring
in Si. By construction, t1 can be only related to the ﬁrst and the last element of Si.
Since the cutting is performed using non-crossing paths in P, the regions P[Φ′] for the obtained
subproblems can only share their boundaries, that is, if some v is strictly inside one of the curves Φ′,
then it it is not strictly inside another obtained curve Φ′′. Therefore, if we proceeded with the
above subproblems recursively, we would not aggregate or report any vertex of v ∈ΠP (B) \ ∂P
twice.
However, we still need to report/aggregate vertices that lie on paths π1, . . . , πl strictly
inside the curve Φ.
We now discuss how this strategy is implemented.
Let us ﬁrst consider
solving the subproblems recursively.
We handle all the obtained base case instance of types 1
and 2 as explained before. If x1 = sg, then by Lemma 5.6, the total time required for this is
O
��l
i=1(|Si| + 1)
�
= O((p −g) + l). But note that l ≤p −g, so in fact the bound is O(p −g).
To handle the instance (S0 ∪T, Φs1,x1 ·πR
1 ·Φt1,s1), we simply replace (B, Φ) with it and proceed
with solving it using the algorithm for the general case.
To this end, we set S := S0 ∪{t1},
T := {t2, . . . , tq} and update Z in the data structures L, LR to S0 by removing elements. Then,
invariant (1) is satisﬁed by Lemma 5.7, and invariants (2), (3) and (4) are satisﬁed by construction.
This way, in �O(∆) time we reduce the instance (B, Φ) by ∆= |S| −|S0| = p −g vertices. Recall
that Z = S \ {sp} implies that g < p. Thus, ∆≥1 and the sizes of B and T strictly decrease.
Let us now discuss how to aggregate/report the vertices of ΠP (B) \ ∂P that lie on any of the
paths π1, . . . , πl (that are not handled in any of the subproblems), but at the same time lie strictly
inside Φ (before altering (B, Φ)). Since Φ is formed of either the edges of the hole h, or from the
paths π{u,v}, and each πi is contained in P[Φ], equivalently we need to aggregate the vertices of
ΠP (B) \ ∂P on the paths π1, . . . , πl that do not lie on Φ.
Observe that since x1, . . . , xl lie on Φ in that order, and the paths π1, . . . , πl all lie in P[Φ]
and are non-crossing by Lemma 5.2, for any three i < j < k, we have V (πi) ∩V (πk) ⊆V (πj).
As a result, any vertex on these paths is included in precisely one of the sets V (πi) \ V (πi−1), for
i = 1, . . . , l and V (π0) := ∅. Moreover, in Lemma 5.9 we will show that each πi can possibly have
a non-empty intersection with O(1) parts (between neighboring elements of B) of Φ, that we can
also identify in O(1) time. Since, by Lemma 5.2, for every path π{u,v}, the intersection of π{u,v}
with πi is either empty or forms a subpath of πi, aggregating or reporting the required vertices of
πi boils down to aggregating or reporting the vertices of V (P) \ ∂P on some O(1) subpaths of πi
that form what remains from πi after removing O(1) of its intersections with other paths πu,v.
**Lemma 5.9. Consider the moment when the split into subproblems happens. Suppose xi = sj. Let**
u, v ∈B be neighboring on Φ, so that u comes before v in the counterclockwise order ≺h on Φ.
Then (V (πi)∩V (Φu,v))\∂P̸ = ∅implies that u = sj′ for some j′ ∈{1, . . . , p} such that |j −j′| ≤2.
Proof. Recall that the curve is πi is either the path π{xi,t1} or its reverse. Let us only consider the
case when π{xi,t1} = πxi,t1; the case when π{xi,t1} = πt1,xi is analogous.
By invariant (3), we have that u, v ∈S since otherwise Φu,v is a part of the curve h and therefore
does not contain any vertices from outside V (h). So {u, v} = {sj′, sj′+1} for some j′ ∈{1, . . . , p−1}.
Let z ∈(V (πi) ∩V (Φu,v)) \ ∂P. If Φu,v = πsj′,sj′+1, then the z →v subpath of Φu,v and the
xi →z subpath of πi together form an sj →sj′+1 path in P, which by invariant (2) implies
17

## Page 18

j′ + 1 ∈{j −1, j, j + 1}, and thus j′ ∈[j −2, j]. If Φu,v = πsj′+1,sj′, then, analogously, there exists
an sj →sj′ path in P, so j′ ∈[j −1, j + 1].
By Lemma 5.9, for each πi, we need to report all vertices of πi from outside ∂P, except those
on the union of at most 6 subpaths of πi. Since the subpaths are always intersections of some
two paths πu,v, we can identify these subpaths using precomputed data in O(1) time. Aggregating
vertex weights not on at most 6 subpaths of πi is the same as aggregating weights on at most 7
disjoint subpaths of πi. Recall that we have precomputed the aggregate weights for all the subpaths
of all the possible πu,v. As a result, aggregating or reporting vertices ΠP (B) \ ∂P that lie on any
of the paths π1, . . . , πl takes O(l) = O(p −g) time.
Lemma 5.10. The general case can be handled in �O(|B|) time.
Proof. Recall that when T = ∅, we have a base instance that can be solved in O(|B|) time.
Every iteration of the main loop that does not involve changing B takes O(polylog n) time and
reduces the size of T by one. But the set T can shrink at most |B| times, so such iterations cost
�O(|B|) time in total. Every other iteration of the main loop involves reducing the size of B by
some ∆> 0 in �O(∆) time. Such iterations clearly cost �O(|B|) time in total as well.
**5.7**
**Handling multiple-hole queries**
In this section we discuss how to drop the simplifying assumption that the query set A ⊆∂P lies
entirely on a single hole of P.
Before we continue, let us remark that in Section 5 we did not fully leverage the fact that the
holes’ bounding cycles of a piece of an r-division with few holes contain vertices from ∂P exclusively.
Indeed, we only used that (i) A lies on a single face h of P, and (ii) that there was no need to
report or aggregate vertices lying on the bounding cycle of h – indeed, in a piece of an r-division
with few holes no vertex of V (P) \ ∂P lies on the bounding cycle of h.
In the following, we will slightly relax the problem: deﬁne ∂∗P to contain all the vertices of P on
the bounding cycles of h1, . . . , hk, and let ∂P be an arbitrary ﬁxed subset of ∂∗P of size O(√r) (but
the set ∂∗P can be possibly larger). Given A ⊆∂P, the query’s objective is to aggregate/report
vertices of ΠP (A)\∂∗P. By the above discussion, the data structure of Section 5 can actually solve
this slightly more general problem within the same bounds. Moreover, as discussed in Section 5.2,
we no longer use the assumption of Theorem 4.3 that ΠP (A) ∩∂P = A which was only required to
reduce to the acyclic case.
Denote by ∂∗
i P, for i = 1, . . . , k, the vertices of ∂∗P that lie on the hole hi.
Recall that
k = O(1). The sets ∂∗
1P, . . . , ∂∗
kP are not necessarily disjoint. We now describe how to reduce the
problem, roughly speaking, to the case when P has one hole less. The reduction will require O(r3)
additional preprocessing and will add only O(|A|) overhead to the query procedure. The reduction
will preserve acyclicity.
**5.7.1**
**Preprocessing**
Suppose ﬁrst that there exist no such s ∈∂∗
i P and t ∈∂∗
j P, where i̸ = j, that s can reach t in P.
This can be clearly checked in O(|P|) = O(r) time by running graph search k times. In this case,
we have that ΠP (A)\∂∗P is a disjoint sum of ΠP (A∩∂∗
i P)\∂∗
i P. Hence, all we do is simply apply
the preprocessing of Section 5 k times, for each hole hi independently, i.e., we set ∂∗P := ∂∗
i P and
∂P := ∂P ∩∂∗
i P in the i-th single-hole data structure. This takes �O(kr3) = �O(r3) time.
Let us now assume that such s, t exist and pick them so that we can ﬁnd a simple s →t path Q
such that V (Q) ∩∂∗P = {s, t} (we might possibly have s = t). For example, such a path Q can be
18

## Page 19

found in O(r) time by computing, for each pair of holes of P, a shortest path between these two
holes, and taking the shortest out of these paths as Q. Wlog. let us renumber the sets ∂∗
i P so that
s ∈∂∗
1P and t ∈∂∗
2P.
For every b ∈∂P, we compute (i) the ﬁrst vertex ﬁrstb on the path Q that b can reach in P,
and (ii) the last vertex lastb on Q that can reach b in P. All the vertices ﬁrstb and lastb (that exist)
can be computed in O(r) time via graph search (see e.g. [Tho04]).
Let us obtain a graph P ′ from P by cutting along the path Q = u1 . . . uq = s →t. Formally, the
path Q is replaced with two copies Q′ = u′
1 . . . u′
q and Q′′ = u′′
1 . . . u′′
q, but the copies u′
i, u′′
i of the
vertex ui are not connected. Neither the vertices nor the edges of Q are contained in the graph P ′,
only Q′ and Q′′ are there. For all v ∈V (P) \ V (Q), for convenience we set v′ = v′′ := v. Clearly,
P ′ is acyclic if P is acyclic.
We set the boundary of P ′ to be:
∂P ′ := ∂P \ {s, t} ∪
�
b∈∂P
{ﬁrst′
b, ﬁrst′′
b, last′
b, last′′
b}.
Note that the two holes h1, h2 of P are merged into a single hole h in P ′. As a result, and since
all the vertices ∂P ′ \∂P lie on h, P ′ has less holes (that is, faces containing boundary vertices ∂P ′)
than P. Moreover, we have (recall that ∂∗P ′ denotes all vertices on the holes of P ′):
∂∗P ′ := ∂∗P \ {s, t} ∪V (Q′) ∪V (Q′′).
Observe that |P ′| ≤3|P| = O(r) and |∂P ′| ≤5|∂P| so |∂P ′| = O(√r). We recursively build a data
structure supporting desired queries A′ ⊆∂P ′ on the graph P ′ as deﬁned above.
Finally, for all the subpaths R of Q we precompute the aggregate weights of all the vertices of
V (R) \ ∂∗P = V (R) \ {s, t}. This can be done in O(r3) time using a brute force algorithm.
Since the piece P has initially size O(r), |∂P| = O(√r) and ∂P lies on k = O(1) holes of P,
after at most k −1 recursive preprocessing steps we will arrive at the single-hole case (when a pair
s, t cannot be found, possibly because k = 1). In each of the recursive data structures, the input
piece has size 2O(k) · O(r) = O(r), and has |∂P| = 2O(k) · O(√r) = O(√r). At each of the O(1)
recursive levels, the additional preprocessing takes O(r3) time.
**5.7.2**
**Query**
Given A ⊆∂P, the query procedure is as follows.
If P is at the lowest level of the recursive
data structure, then we split A into O(1) sets Ai = A ∩∂∗
i P. For each of the sets Ai we run the
single-hole query procedure independently. Since there are no paths between boundary vertices on
distinct holes, we can aggregate the results in an obvious way. This is justiﬁed by the fact that
ΠP (A) \ ∂∗P is a disjoint union of the O(1) sets ΠP(A ∩∂∗
i P) \ ∂∗P. Clearly, the query algorithm
runs in �O(|A|) time in this case.
Otherwise, if P is not leaf-level in the recursion, let ≺denote the natural order on vertices of
the path Q. Let f = min≺{ﬁrsta : a ∈A} and l = max≺{lasta : a ∈A}. We construct the set
A′ :=
�
(A ∩∂P ′) ∪{f ′, f ′′, l′, l′′}
if f ⪯l,
A ∩∂P ′
otherwise.
Clearly, A′ ⊆∂P ′ can be constructed in O(|A|) time and has size O(|A|). Note that A′ might not
satisfy ΠP ′(A′)∩∂P ′ = A′, but we do not need that assumption if P ′ is acyclic, as discussed before.
We issue a query about A′ to the data structure built recursively on P ′ which has one hole less. That
19

## Page 20

data structure produces aggregate weight σ of ΠP ′(A′) \ ∂∗P ′ or an iterator reporting the elements
of that set in O(1) time. To lift σ to the desired aggregate weight for ΠP (A) \ ∂∗P, we simply
additionally add the precomputed aggregate weight of the subpath Q[f, l] (except s, t ∈∂∗P). To
lift the reporting function, we simply report the vertices V (Q[f, l]) \ {s, t} after we have ﬁnished
reporting ΠP ′(A′)\∂∗P ′. Recall that V (Q[f, l])\{s, t} is disjoint with ΠP ′(A′)\∂∗P ′ by construction.
We now prove the correctness of this algorithm.
Lemma 5.11. For any A ⊆∂P, we have ΠP (A) \ ∂∗P = (ΠP ′(A′) \ ∂∗P ′) ∪(V (Q[f, l]) \ {s, t}).
Proof. Let us start with the “⊇” direction. Suppose ﬁrst that v ∈ΠP ′(A′) \ ∂∗P ′. Since we have
V (P ′) \ V (P) ⊆∂∗P ′ and s, t /∈V (P ′), we have v ∈V (P) \ ∂∗P. Moreover, v lies on some path
R′ = a →b between vertices of A′ in P ′. Since every vertex (edge) of P ′ is a either an original
vertex (edge, resp.) or a copy of a vertex (edge, resp.) of P, there is a path R = a0 →b0 in P
whose R′ is a copy of. If a0, b0 ∈A, then we have v ∈ΠP (A) \ ∂∗P immediately. Otherwise, if e.g.,
a0 /∈A, then f ⪯l and a0 ∈{f, l}. However, by the deﬁnition of f, f is reachable from a vertex
c ∈A. Since a path f →l exists in P as a subpath of Q, l is reachable from c as well. As a result,
even if a0 /∈A, a0, and thus also v, is reachable from A in P. Analogously one can argue that b0,
and thus also v, can reach A in P.
Now consider v ∈V (Q[f, l]) \ {s, t}. Then, f ⪯l and we similarly argue that v can be reached
from f and can reach l and as a result can reach and can be reached from A in P.
Let us now move to the more challenging “⊆” direction. Consider some v ∈ΠP(A)\∂∗P. There
exists a path R = a →v →b in P with a, b ∈A. If V (R) ∩V (Q) = ∅, then the path R is preserved
in the graph P ′. Moreover, a, b ∈∂P \ {s, t} and thus a, b ∈A′. We obtain v ∈ΠP ′(A′) \ ∂∗P ′ by
v /∈V (Q), as desired. Hence, in the following we assume V (R) ∩V (Q)̸ = ∅. Note that this also
implies that f ⪯l since A can reach Q and be reached from Q.
First suppose that v ∈V (Q) ∩V (R). Since v /∈∂∗P, v /∈{s, t}. By the deﬁnition of f, l, we
have f ⪯v ⪯l and thus v ∈V (Q[f, l]) \ {s, t}, as desired.
Now assume v ∈V (R) \ V (Q). Note that v /∈∂∗P ∪V (Q) implies v = v′ = v′′ /∈∂∗P ′. Let x, y
denote the ﬁrst and the last vertex of Q on R, respectively. Let R = R1 ·R2 ·R3, where R1 = a →x
and R3 = y →b. Observe that the paths R1 and R3 are preserved in P ′, except R1 reaches a copy
of x, and R3 starts at a copy of y. Moreover, note that x ⪯y by acyclicity, and thus we have
f ⪯ﬁrsta ⪯x ⪯y ⪯lastb ⪯l.
Consider the case v ∈V (R1) \ V (Q). Assume wlog. that R1 joins the path Q in P in such a
way that R1 is preserved as R′
1 = a′ →x′ in P ′. Now, observe that the path R′
1 · Q′[x′, l′] is an
a′ →l′ path in P ′ containing the vertex v, and l′ ∈A′. If a /∈{s, t}, then clearly also a′ ∈A′.
Otherwise, if a = s, then f = s and thus a′ = f ′, whereas if a = t, then l = t and thus a′ = l′.
In all cases {a′, l′} ⊆A′. As a result, indeed v ∈ΠP ′(A′) \ ∂∗P ′. One can proceed with the case
v ∈V (R3) \ V (Q) symmetrically.
Finally, suppose v ∈V (R2). Then, split R2 into maximal subpaths with only their endpoints
lying on the path Q. One of the obtained maximal subpaths S = c →d, where c, d ∈V (Q), goes
through v. Again, we have f ⪯ﬁrsta ⪯c ⪯d ⪯lastb ⪯l. Moreover, S is preserved in P ′ as wlog.
the path S′′ = c′′ →d′′. But then Q′′[f ′′, c′′] · S′′ · Q′′[d′′, l′′] is a f ′′ →l′′ path in P ′ that goes
through v. Since f ′′, l′′ ∈A′, we again obtain v ∈ΠP ′(A′) \ ∂∗P ′, as desired.
When queried about the set A, the recursive data structures are passed a set A′ with |A′| =
|A| + O(1) = O(|A|). As a result, the query time is dominated by the �O(|A′|) = �O(|A|) time used
by the bottommost single-hole data structure. This ﬁnishes the proof of Theorem 4.3.
20

## Page 21

**5.8**
**The existential reachability data structure**
In this section, we prove the following.
**Lemma 5.3. In �O(r) time one can construct a data structure maintaining an (initially empty) set**
Z ⊆∂P ∩V (h) and supporting the following operations in O(polylog n) time:
• insert or delete a single b ∈∂P ∩V (h) either to or from Z.
• for any query vertex v ∈(∂P ∩V (h)) \ Z, ﬁnd any z ∈Z (if exists) that v can reach in P.
We will use the following property of reachability between vertices lying on a single face of a
planar digraph P essentially proved in [IKŁS17].
**Lemma 5.12. [IKŁS17] Let the vertices Y lie on a single face h of a planar digraph P. Then in**
�O(|P| + |Y |2) time one can compute O(|Y |) pairs of subsets Si, Ti ⊆Y such that:
1. For any i, the elements Ti have an associated linear order ≺i.
2. For any i and s ∈Si, there exist such vertices li,s, ri,s that for any t ∈Ti, s can reach t in P
iﬀli,s ⪯i t ⪯i ri,s.
3. Every v ∈Y is contained in O(log |Y |) subsets Si and O(log |Y |) subsets Ti.
4. For any u, v ∈Y , if u can reach v in P, then there exists such i that (u, v) ∈Si × Ti.
Proof sketch. Split Y into two disjoint parts A, B such that A ∪B = Y , |A|, |B| ≤⌈|Y |/2⌉, and
both A, B appear consecutively on h. Let T denote the vertices of B that can be reached from
some vertex of A in P. Similarly, let S denote the vertices of A that can reach B in P. Let ≺be
the counterclockwise order on T starting with the vertex that appears earliest after a vertex of A
in the counterclockwise order of Y on h. One can easily prove (see [IKŁS17]) that each s ∈S can
in fact reach some number of vertices that appear consecutively in T. As a result, there exist such
ls, rs ∈T that for any t ∈T, s can reach t in P iﬀls ⪯t ⪯rs.
We include the pair (S, T) along with the order ≺, and the vertices {ls, rs : s ∈S} in the
constructed family. The obtained pair encodes the reachability from the vertices A to vertices B
in P: if a ∈A can reach b ∈B in T then clearly a ∈S, b ∈T. Note that the subsets S, T can be
constructed in �O(|Y |2) time if only we can answer reachability queries in P in O(polylog n) time.
This is indeed possible after �O(|P|) time preprocessing [Tho04].
Symmetrically we can deal with the reachability from the vertices B to the vertices A in P.
It remains to handle reachability between pairs of vertices inside the set A, and between pairs
inside B. This is done recursively. Since |A|, |B| ≤⌈|Y |/2⌉, each vertex of the original input set Y
will appear in O(log |Y |) recursive calls, and thus in O(log |Y |) sets Si or Ti. It is easy to check
that the algorithm produces all the pairs (Si, Ti) in �O(|Y |2) time.
Proof of Lemma 5.3. We ﬁrst compute the sets (Si, Ti) from Lemma 5.12 applied to Y := ∂P ∩V (h)
(along with the orderings ≺i, and all the vertices li,v, ri,v) in �O(|P|+|∂P|2) = �O(r) time. The data
structure simply stores the sets Ti ∩Z for all i sorted according to ≺i, each of them in a balanced
binary search tree. Note that when an element b is inserted or removed from Z, it is enough to
update O(log r) sets Ti ∩Z as b is contained in O(log r) sets Ti.
To answer a query, that is, ﬁnd a vertex z ∈Z reachable from a query vertex v, for each of the
O(log r) indices i such that v ∈Si we check whether the set Ti ∩Z contains an element z between
li,s and ri,s inclusive, wrt. ≺i. This clearly takes O(log r) time. By Lemma 5.12, s can reach a
vertex in Z if and only if at least one z is found this way.
We conclude that both the update and the query time of the data structure is O(log2 r).
21

## Page 22

#### 6
#### Fully dynamic #SSR in planar digraphs
In this section, we sketch how a data structure summarized by the below lemma can be obtained.
**Lemma 6.1. Let G be a planar digraph subject to planarity-preserving edge insertions and dele-**
tions. There exists a data structure with �O(n4/5) worst-case update time supporting counting the
vertices reachable from a query vertex s in �O(n4/5) time.
We again use the same template as in Sections 3 and 4: as a base, we maintain an r-division R
with few holes, along with the piecewise reachability certiﬁcates XP .
In addition, we leverage the additively-weighted Voronoi diagram data structure of [GKM+21].
Before stating the interface and characteristics of that data structure, we need to introduce some
more notation. Suppose H is a non-negatively weighted plane digraph. Let ∂H ⊆V (H) be the set
of vertices of H lying on some O(1) ﬁxed faces of H (and containing all vertices of these faces) and
such that every v ∈V (H) is reachable from ∂H in H. Let ω : ∂H →R be a weight function such
that for any v ∈V (H), ω(s) + distH(s, v) has a unique minimizer s ∈∂H. The additively weighted
Voronoi diagram wrt. ω is the partition of V (H) into disjoint subsets (cells) Vor(s), s ∈∂H, such
that Vor(s) contains precisely the vertices v such that s minimizes ω(s) + distH(s, v). Note that
by our assumptions on H, if v ∈Vor(s), then ω(s) + distH(s, v)̸ = ∞. The complexity |∂Vor(s)| of
Vor(s) is deﬁned to be the number of faces of H whose vertices include elements of Vor(s) and at
least two other cells. One can prove that �
s∈∂H |∂Vor(s)| = O(|∂H|) [GKM+21].
**Theorem 6.2. [GKM+21] Let H be as deﬁned above. In �O**
�
|H| · |∂H|2�
one can construct a data
structure such that for any ω satisfying the assumptions outlined above, it can build a representation
of the additively-weighted Voronoi diagram wrt. ω in �O(|∂H|) time. The representation allows,
among others, computing all the cell sizes |Vor(s)|, s ∈∂H, in �O(|∂H|) total time.
Proof sketch. This is essentially a special case of [GKM+21, Theorem 1.1]. There, it is stated that
after the representation is built, one can compute, for any s ∈∂H, the furthest vertex v ∈Vor(s)
(i.e., v maximizing ω(s)+distH(s, v)) in �O(|∂Vor(s)|) time. But in [GKM+21, Section 7], where this
functionality is described, it is evident that within the same time bound one can in fact aggregate
over Vor(s) (that is, compute the maximum or e.g., sum) arbitrary vertex labels ℓ(v) (which could
even dependent on s; as long as they are computable in �O(|H| · |∂H|2) total additional time).
Therefore, if we assign the label 1 to every vertex of H, in �O(|∂Vor(s)|) time one can compute
|Vor(s)|. Through all s ∈|∂H|, this is �O(|∂H|) time as mentioned before.
For each piece P, besides the certiﬁcate XP , we additionally maintain a data structure AVP of
Theorem 6.2 for a “proxy” P ′ obtained from P by removing all the vertices v ∈V (P) unreachable
from ∂P. Observe that AVP can be computed in �O(|P| · (|∂P|)2) = �O(r2) time. By Theorem 2.1,
updating R along with all other associated piecewise data structures costs �O(r2) worst-case time.
Upon query about the number of vertices reachable from s ∈V , we proceed as follows. We
ﬁrst compute the subset S ⊆∂R of boundary vertices reachable from s in G by running graph
search from s on the graph Ps ∪X = Ps ∪�
P ∈R XP , where Ps is an arbitrarily chosen piece with
containing s. This is correct by Lemma 3.3 and costs �O(r +n/√r) time. From the graph search we
also retrieve the vertices T ⊆V (Ps) \ ∂Ps that s can reach. Then, for each P̸ = Ps we construct a
weight function ωP such that if ∂P ∩S = {a1, . . . , ak} and ∂P \S = {b1, . . . , bl}, then: ω(ai) := i·M
for all i and ω(bj) := (k + j) · M for all j, where M = V (P). Note that since distP ′(∂P, v) < M for
any v ∈V (P ′), the cell is uniquely determined for every v ∈V (P ′). Namely, if v can be reached
from ai ∈∂P ∩S in P ′, and i is minimized (and thus s can reach v through S), then v ∈Vor(ai).
Otherwise, v can be reached from some bj ∈∂P \S in P, where j is minimized (and s cannot reach
22

## Page 23

v through S), and then v ∈Vor(bj). We conclude that �k
i=1 Vor(ai) contains precisely the vertices
SP ⊆V (P) (including ∂P ∩S) that s can reach via paths through ∂P. By Theorem 6.2, their
number |SP| = �k
i=1 |Vor(ai)| can be computed in �O(√r) time. In fact, these are all vertices that s
can reach in P: since P̸ = Ps, either s /∈V (P) or s ∈∂R, so every vertex in P can be reached from
s only via some boundary vertex of P anyway. We conclude that we can count vertices reachable
from s in G by computing:
|S| + |T| +
�
Ps̸=P ∈R
(|SP | −|S ∩∂P|) .
The query time is thus �O(r + n/√r). By picking r = n2/5, we make both the query time and the
worst-case update time �O(n4/5).
#### References
[AW14]
Amir Abboud and Virginia Vassilevska Williams. Popular conjectures imply strong
lower bounds for dynamic problems. In 55th IEEE Annual Symposium on Foundations
of Computer Science, FOCS 2014, pages 434–443. IEEE Computer Society, 2014.
[BDP21]
Aaron Bernstein, Aditi Dudeja, and Seth Pettie. Incremental SCC maintenance in
sparse graphs. In 29th Annual European Symposium on Algorithms, ESA 2021, volume
204 of LIPIcs, pages 14:1–14:16. Schloss Dagstuhl - Leibniz-Zentrum f¨ur Informatik,
2021.
[BFGT16]
Michael A. Bender, Jeremy T. Fineman, Seth Gilbert, and Robert E. Tarjan.
A
new approach to incremental cycle detection and related problems.
ACM Trans.
Algorithms, 12(2):14:1–14:22, 2016.
[BGS20]
Aaron Bernstein, Maximilian Probst Gutenberg, and Thatchaphol Saranurak. Deter-
ministic decremental reachability, scc, and shortest paths via directed expanders and
congestion balancing. In 61st IEEE Annual Symposium on Foundations of Computer
Science, FOCS 2020, pages 1123–1134. IEEE, 2020.
[BPW19]
Aaron Bernstein, Maximilian Probst, and Christian Wulﬀ-Nilsen.
Decremental
strongly-connected components and single-source reachability in near-linear time. In
Proceedings of the 51st Annual ACM SIGACT Symposium on Theory of Computing,
STOC 2019, pages 365–376. ACM, 2019.
[CHI+16]
Shiri Chechik, Thomas Dueholm Hansen, Giuseppe F. Italiano, Jakub Łącki, and
Nikos Parotsidis. Decremental single-source reachability and strongly connected com-
ponents in ˜o(m√n) total update time. In IEEE 57th Annual Symposium on Foun-
dations of Computer Science, FOCS 2016, pages 315–324. IEEE Computer Society,
2016.
[CK22]
Panagiotis Charalampopoulos and Adam Karczmarz.
Single-source shortest paths
and strong connectivity in dynamic planar graphs. J. Comput. Syst. Sci., 124:97–111,
2022.
[CKL+23]
Li Chen, Rasmus Kyng, Yang P. Liu, Simon Meierhans, and Maximilian Probst Guten-
berg. Almost-linear time algorithms for incremental graphs: Cycle detection, sccs, s-t
shortest path, and minimum-cost ﬂow, 2023.
23

## Page 24

[DS07]
Krzysztof Diks and Piotr Sankowski. Dynamic plane transitive closure. In Algorithms
- ESA 2007, 15th Annual European Symposium, Proceedings, pages 594–604, 2007.
[EFL18]
JeﬀErickson, Kyle Fox, and Luvsandondov Lkhamsuren. Holiest minimum-cost paths
and ﬂows in surface graphs. In Proceedings of the 50th Annual ACM SIGACT Sym-
posium on Theory of Computing, STOC 2018, pages 1319–1332, 2018.
[FR06]
Jittat Fakcharoenphol and Satish Rao. Planar graphs, negative weight edges, shortest
paths, and near linear time. J. Comput. Syst. Sci., 72(5):868–889, 2006.
[Fre85]
Greg N. Frederickson. Data structures for on-line updating of minimum spanning
trees, with applications. SIAM J. Comput., 14(4):781–798, 1985.
[Fre87]
Greg N. Frederickson.
Fast algorithms for shortest paths in planar graphs, with
applications. SIAM J. Comput., 16(6):1004–1022, 1987.
[Gab00]
Harold N. Gabow. Path-based depth-ﬁrst search for strong and biconnected compo-
nents. Inf. Process. Lett., 74(3-4):107–114, 2000.
[GKM+21]
Pawel Gawrychowski, Haim Kaplan, Shay Mozes, Micha Sharir, and Oren Weimann.
Voronoi diagrams on planar graphs, and computing the diameter in deterministic
˜o(n5/3) time. SIAM J. Comput., 50(2):509–554, 2021.
[GMWW18] Pawel Gawrychowski, Shay Mozes, Oren Weimann, and Christian Wulﬀ-Nilsen. Better
tradeoﬀs for exact distance oracles in planar graphs. In Proceedings of the Twenty-
Ninth Annual ACM-SIAM Symposium on Discrete Algorithms, SODA 2018, New
Orleans, LA, USA, January 7-10, 2018, pages 515–529. SIAM, 2018.
[GRST21]
Gramoz Goranci, Harald R¨acke, Thatchaphol Saranurak, and Zihan Tan. The ex-
pander hierarchy and its applications to dynamic graph algorithms. In Proceedings
of the 2021 ACM-SIAM Symposium on Discrete Algorithms, SODA 2021, Virtual
Conference, January 10 - 13, 2021, pages 2212–2228. SIAM, 2021.
[HdLT01]
Jacob Holm, Kristian de Lichtenberg, and Mikkel Thorup. Poly-logarithmic deter-
ministic fully-dynamic algorithms for connectivity, minimum spanning tree, 2-edge,
and biconnectivity. J. ACM, 48(4):723–760, 2001.
[HHK+23]
Shang-En Huang, Dawei Huang, Tsvi Kopelowitz, Seth Pettie, and Mikkel Thorup.
Fully dynamic connectivity in o(log n(loglog n)2) amortized expected time. Theoret-
iCS, 2, 2023.
[HKM+12]
Bernhard Haeupler, Telikepalli Kavitha, Rogers Mathew, Siddhartha Sen, and
Robert Endre Tarjan. Incremental cycle detection, topological ordering, and strong
component maintenance. ACM Trans. Algorithms, 8(1):3:1–3:33, 2012.
[HKNS15]
Monika Henzinger, Sebastian Krinninger, Danupon Nanongkai, and Thatchaphol
Saranurak. Unifying and strengthening hardness for dynamic problems via the online
matrix-vector multiplication conjecture. In Proceedings of the Forty-Seventh Annual
ACM on Symposium on Theory of Computing, STOC 2015, pages 21–30. ACM, 2015.
[IKŁS17]
Giuseppe F. Italiano, Adam Karczmarz, Jakub Łącki, and Piotr Sankowski. Decre-
mental single-source reachability in planar digraphs. In Proceedings of the 49th Annual
24

## Page 25

ACM SIGACT Symposium on Theory of Computing, STOC 2017, pages 1108–1121.
ACM, 2017.
[IP01]
Russell Impagliazzo and Ramamohan Paturi. On the complexity of k-sat. J. Comput.
Syst. Sci., 62(2):367–375, 2001.
[Kle05]
Philip N. Klein. Multiple-source shortest paths in planar graphs. In Proceedings of
the Sixteenth Annual ACM-SIAM Symposium on Discrete Algorithms, SODA 2005,
pages 146–155, 2005.
[KMNS17]
Haim Kaplan, Shay Mozes, Yahav Nussbaum, and Micha Sharir. Submatrix maximum
queries in monge matrices and partial monge matrices, and their applications. ACM
Trans. Algorithms, 13(2):26:1–26:42, 2017.
[KMS13]
Philip N. Klein, Shay Mozes, and Christian Sommer. Structured recursive separator
decompositions for planar graphs in linear time. In Symposium on Theory of Com-
puting Conference, STOC’13, Palo Alto, CA, USA, June 1-4, 2013, pages 505–514,
2013.
[KS98]
Philip N. Klein and Sairam Subramanian. A fully dynamic approximation scheme for
shortest paths in planar graphs. Algorithmica, 22(3):235–249, 1998.
[KS23]
Adam Karczmarz and Marcin Smulewicz. On fully dynamic strongly connected com-
ponents. In 31st Annual European Symposium on Algorithms, ESA 2023, September
4-6, 2023, Amsterdam, The Netherlands, volume 274 of LIPIcs, pages 68:1–68:15.
Schloss Dagstuhl - Leibniz-Zentrum f¨ur Informatik, 2023.
[LP21]
Yaowei Long and Seth Pettie. Planar distance oracles with better time-space tradeoﬀs.
In Proceedings of the 2021 ACM-SIAM Symposium on Discrete Algorithms, SODA
2021, Virtual Conference, January 10 - 13, 2021, pages 2517–2537. SIAM, 2021.
[Łą13]
Jakub Łącki.
Improved deterministic algorithms for decremental reachability and
strongly connected components. ACM Trans. Algorithms, 9(3):27:1–27:15, 2013.
[RZ08]
Liam Roditty and Uri Zwick. Improved dynamic reachability algorithms for directed
graphs. SIAM J. Comput., 37(5):1455–1471, 2008.
[San05]
Piotr Sankowski. Subquadratic algorithm for dynamic shortest distances. In Com-
puting and Combinatorics, 11th Annual International Conference, COCOON 2005,
Kunming, China, August 16-29, 2005, Proceedings, volume 3595 of Lecture Notes in
Computer Science, pages 461–470. Springer, 2005.
[Sha81]
M. Sharir. A strong-connectivity algorithm and its applications in data ﬂow analysis.
Computers & Mathematics with Applications, 7(1):67–72, 1981.
[Sub93]
Sairam Subramanian. A fully dynamic data structure for reachability in planar di-
graphs. In Algorithms - ESA ’93, First Annual European Symposium, Bad Honnef,
Germany, September 30 - October 2, 1993, Proceedings, pages 372–383, 1993.
[Tar72]
Robert Endre Tarjan.
Depth-ﬁrst search and linear graph algorithms.
SIAM J.
Comput., 1(2):146–160, 1972.
25

## Page 26

[Tho04]
Mikkel Thorup. Compact oracles for reachability and approximate distances in planar
digraphs. J. ACM, 51(6):993–1024, 2004.
[vdBNS19]
Jan van den Brand, Danupon Nanongkai, and Thatchaphol Saranurak.
Dynamic
matrix inverse: Improved algorithms and matching conditional lower bounds. In 60th
IEEE Annual Symposium on Foundations of Computer Science, FOCS 2019, pages
456–480. IEEE Computer Society, 2019.
[Wil05]
Ryan Williams. A new algorithm for optimal 2-constraint satisfaction and its impli-
cations. Theor. Comput. Sci., 348(2-3):357–365, 2005.
[Wul13]
Christian Wulﬀ-Nilsen.
Faster deterministic fully-dynamic graph connectivity.
In
Proceedings of the Twenty-Fourth Annual ACM-SIAM Symposium on Discrete Algo-
rithms, SODA 2013, New Orleans, Louisiana, USA, January 6-8, 2013, pages 1757–
1769. SIAM, 2013.
26
