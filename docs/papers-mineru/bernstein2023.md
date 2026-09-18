# Decremental Strongly-Connected Components and Single-Source Reachability in Near-Linear Time

**Aaron Bernstein**<sup>∗</sup> **Maximilian Probst**† **Christian Wulff-Nilsen**‡

**March 15, 2019**

## Abstract

**Computing the Strongly-Connected Components (SCCs) in a graph** $G \; = \; ( V , E )$ **is known to take only** $O ( m + n )$ **time using an algorithm by Tarjan from 1972[SICOMP 72] where** $m = | E | ,   n = | V |$ **. For fully-dynamic graphs, conditional lower bounds provide evidence that the update time cannot be improved by polynomial factors over recomputing the SCCs from scratch after every update. Nevertheless, substantial progress has been made to find algorithms with fast update time for** decremental **graphs, i.e. graphs that undergo edge deletions.**

**In this paper, we present the first algorithm for general decremental graphs that main**tains the SCCs in total update time $\tilde { O } ( m ) ^ { 1 }$ O(m **, thus only a polylogarithmic factor from the optimal running time. Previously such a result was only known for the special case of planar graphs [Italiano et al, STOC 17]. Our result should be compared to the formerly** best algorithm for general graphs achieving $\tilde { O } ( m \sqrt { n } )$ **total update time by Chechik et al.** [FOCS 16] which improved upon a breakthrough result leading to $O ( m n ^ { 0 . 9 + o ( 1 ) } )$ total up**date time by Henzinger, Krinninger and Nanongkai [STOC 14, ICALP 15]; these results in turn improved upon the longstanding bound of O(mn) by Roditty and Zwick [STOC 04].**

**All of the above results also apply to the decremental Single-Source Reachability (SSR)** problem which can be reduced to decrementally maintaining SCCs. A bound of $O ( m n )$ to**tal update time for decremental SSR was established already in 1981 by Even and Shiloach [JACM 81].**

**Using a well known reduction, we use our decremental result to achieve new update/querytime trade-offs in the fully dynamic setting. We can maintain the reachability of pairs** $S \times V ,   S \subseteq V$ in fully-dynamic graphs with update time $\begin{array} { r } { \tilde { O } ( \frac { | S | m } { t } ) } \end{array}$ **and query time** $O ( t )$ **for all** $t \in [ 1 , | S | ]$ **; this matches the best All-Pairs Reachability algorithm for** $S = V$ **[Łącki, TALG 13].**

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>∗</sup>Rutgers University New Brunswick, Department of Computer Science</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">†BARC, University of Copenhagen, Universitetsparken 1, Copenhagen 2100, Denmark, The author is supported by Basic Algorithms Research Copenhagen (BARC), supported by Thorup’s Investigator Grant from the Villum Foundation under Grant No. 16582.</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">‡Department of Computer Science, University of Copenhagen. This research is supported by the Starting Grant 7027-00050B from the Independent Research Fund Denmark under the Sapere Aude research career programme.</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">Õ(f(n))</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">g(n) = (f(n)) g(n) = (f(n)po y og(n))</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">1We use  notation to suppress logarithmic factors, i.e.  Õ if  O l l .</span></small>

## 1 Introduction

**For a directed graph** $G = ( V , E )$ **, with** $n = | V | , m = | E |$ **, the Strongly-Connected Components** (SCCs) of G are the sets of the unique partition of the vertex set V into sets $V _ { 1 } , V _ { 2 } , . . , V _ { k }$ such that for any two vertices $u \in V _ { i } , v \in V _ { j }$ **, there exists a directed cycle in G containing u and v if and only if** $i = j$ **. In the Single-Source Reachability (SSR) problem, we are given a distinguished source** $r \in V$ **and are asked to find all vertices in V that can be reached from r. The SSR problem can be reduced to finding the SCCs by inserting edges from each vertex in V to the distinguished source r.**

**Finding SCCs in static graphs in** $O ( m + n )$ **time is well-known since 1972[Tar72] and is commonly taught in undergraduate courses, also appearing in CLRS[Cor+09].**

**In this paper we focus on maintaining SCCs in a dynamic graph. The most general setting is the fully dynamic one, where edges are being inserted and deleted into the graph. While many connectivity problems for undirected graphs have been solved quite efficiently [HDT01; Wul13; Tho00; Tho07; Hua+17; NSW17], in fully-dynamic graphs, the directed versions of these problems have proven to be much harder to approach.**

**In fact, Abboud and Vassilevska[AW14] showed that any algorithm that can maintain** whether there are more than 2 SCCs in a fully-dynamic graph with update time $O ( m ^ { 1 - \epsilon } )$ and query time $O ( m ^ { 1 - \epsilon } )$ **, for any constant** $\epsilon \; > \; 0$ **, would imply a major breakthrough on** SETH. The same paper also suggests that $O ( m ^ { 1 - \epsilon } )$ update time and query time $O ( n ^ { 1 - \epsilon } )$ **for maintaining the number of reachable vertices from a fixed source would imply a breakthrough for combinatorial Matrix Multiplication.**

**For this reason, research on dynamic SCC and dynamic single-source reachability has focused on the partially dynamic setting (decremental or incremental). In this paper we study the** decremental **setting, where the original graph only undergoes edge deletions (no insertions). We note that both lower bounds above extend to decremental algorithms with** worst-case update time $O ( m ^ { 1 - \epsilon } )$ **, so all existing results focus on the amortized update time.**

**The first algorithm to maintain SSR faster than recomputation from scratch achieved total update time O(mn)[ES81]. The same update time for maintaining SCCs was achieved by a randomized algorithm by Roddity and Zwick[RZ08]. Their algorithm also establishes that any algorithm for maintaining SSR can be turned into a randomized algorithm to maintain the SCCs incurring only an additional constant multiplicative factor in the running time. Later, Łącki[Łąc13] presented a simple deterministic algorithm that matches** $O ( m n )$ **total update time and that also maintains the transitive closure. For several decades, it was not known how to get beyond total update time** $O ( m n )$ **,** until a recent breakthrough by Henzinger, **Krinninger and Nanongkai[HKN14b; HKN15] reduced the total update time to expected time** $O ( \operatorname* { m i n } ( \tilde { m } ^ { 7 / 6 } n ^ { 2 / 3 } , \tilde { m } ^ { 3 / 4 } \tilde { n ^ { 5 / 4 + o ( 1 ) } } , m ^ { 2 / 3 } n ^ { 4 / 3 + o ( 1 ) } + m ^ { 3 / 7 } n ^ { 1 2 / 7 + o ( 1 ) } ) ) \stackrel { \circ } { = } O ( m n ^ { 0 . 9 + o ( 1 ) } )$ **Even more recently, Chechik et. al.[Che+16] showed that a clever combination of the algorithms of Roditty** and Zwick, and Łącki can be used to improve the expected total update time to $\tilde { O } ( m \sqrt { n } )$ **. We point out that all of these recent results rely on randomization and in fact no deterministic algorithm for maintaining SCCs or SSR beyond the** $O ( m n )$ **bound is known for general graphs. For planar graphs, Italiano et. al.[Ita+17] presented a deterministic algorithm with total** update time $\tilde { O } ( n )$

**Finally, in this paper, we present the first algorithm for general graphs to maintain SCCs** in $\tilde { O } ( m )$ expected total update time with constant query time, thus presenting the first near**optimal algorithm for the problem. We summarize our result in the following theorem.**

**Theorem 1.1.** Given a graph $G   =   ( V , E )$ with m edges and n vertices, we can maintain a data structure that supports the operations:

$\mathrm { D E L E T E } ( u , v )$ : Deletes the edge $( u , v )$ from the graph $G ,$

$\operatorname { Q U E R Y } ( u , v )$ : Returns whether u and v are in the same $S C C$ in $G ,$

in total expected update time $O ( m \log ^ { 4 } n )$ and with worst-case constant query time. The same time bounds apply to answer for a fixed source vertex $s \in V$ queries on whether a vertex $v \in V$ can be reached from s. The bound holds against an oblivious adaptive adversary.

**Our algorithm makes the standard assumption of an oblivious adversary which does not have access to the coin flips made by the algorithm. But our algorithm does NOT require the assumption of a non-adaptive adversary, which is ignorant of answers to queries as well: the reason is simply that** $\mathrm { S C C }$ **and SSR information is unique, so the answers to queries do not reveal any information about the algorithm. One key exception is that for SSR, if the algorithm is expected to return a witness path, then it does require the assumption of a non-adaptive adversary.**

**A standard reduction described in appendix A also implies a simple algorithm for main**taining reachability from some set $S \subseteq V$ to V in a fully-dynamic graph with vertex set $V$ that is a data structure that answers queries for any $s \in S , v \in V$ **on whether s can reach v.** The amortized expected update time is $\tilde { O } ( | S | m / t )$ and query time $O ( t )$ for every $t \in [ 1 , | S | ]$ **We allow vertex updates, i.e. insertions or deletions of vertices with incident edges, which are more general than edge updates. This generalizes a well-known trade-off result for All-Pairs Reachability[RZ16; Łąc13] with** $\tilde { O } ( n m / t )$ **amortized update time and query time** $O ( t )$ **for every** $t \in [ 1 , n ]$

**Finally, we point out that maintaining SCCs and SSR is related to the more difficult (approximate) shortest-path problems. In fact, the algorithms [ES81; HK95; HKN14b; HKN15] can also maintain (approximate) shortest-paths in decremental directed graphs. For undirected graphs, the decremental Single-Source Approximate Shortest-Path problem was recently solved to near-optimality[HKN14a], and deterministic algorithms[BC16; BC17] have been developed that go beyond the** $O ( m n )$ **barrier. We hope that our result inspires new algorithms to tackle the directed versions of these problems.**

## 2 Preliminaries

**In this paper, we let a graph** $H   =   ( V , E )$ **refer to a directed multi-graph where we allow multiple edges between two endpoints and self-loops but say that a cycle contains at least two distinct vertices. We refer to the vertex set of H by** $V ( H )$ **and the edge set by** $E ( H )$ **. We** denote the input graph by $G ,$ let $V = V ( G )$ and $E = E ( G )$ and define $n = | V |$ and $m = | E |$

**If the context is clear, we simply write sets X instead of their cardinality** $| X |$ **in calculations to avoid cluttering.**

We define a subgraph of H to be a graph $H ^ { \prime }$ with $V ( H ^ { \prime } )   =   V ( H )$ and $E ( H ^ { \prime } ) \subseteq E ( H )$ Observe that this deviates from the standard definition of subgraphs since we require the vertex set to be equivalent. We write $H \setminus E ^ { \prime }$ as a shorthand for the graph $( V ( H ) , E ( H ) \setminus E ^ { \prime } )$ and $H \cup E ^ { \prime }$ as a shorthand for $( V ( H ) , E ( H ) \cup E ^ { \prime } )$ **.** For any $S \subseteq V ( H )$ , we define $E _ { o u t } ^ { H } ( S )$ **to** be the set $( S \times V ( H ) ) \cap E ( H )$ , i.e. the set of all edges in H that emanate from a vertex in $S ;$ we analogously define $E _ { i n } ^ { H } ( S )$ and $E ^ { H } ( S ) = E _ { i n } ^ { H } ( S ) \stackrel { \cdot } { \cup } E _ { o u t } ^ { H } ( S )$ **. If the context is clear, we drop** the superscript and simply write $E _ { i n } ( S ) , E _ { o u t } ( S ) , E ( S )$

**For any graph H, and any two vertices** $u , v \in V ( H )$ **, we denote by dist** ${ } _ { H } ( u , v )$ **the distance from u to v in H. We also define the notion of S-distances for any** $S \subseteq V ( H )$ **where for any pair of vertices** $u , v \in V ( H )$ **, the S-distance dist** $\iota _ { H } ( u , v , S )$ **denotes the minimum number of vertices in** $S \setminus \{ v \}$ **encountered on any path from u to v. Alternatively, the S-distance corresponds** to dist $\boldsymbol { \mathfrak { t } } _ { H ^ { \prime } } ( u , v )$ where $H ^ { \prime }$ is a graph with edges $E _ { o u t } ( S )$ **of** weight 1 and edges $E \setminus E _ { o u t } ( S )$ of weight 0. It therefore follows that for any $u , v \in V ( H )$ , dist ${ } _ { H } ( u , v ) = \mathbf { d i s t } _ { H } ( u , v , V )$

We define the diameter of a graph H by diam $( H )   =   \operatorname { m a x } _ { u , v \in V } \mathbf { d i s t } _ { H } ( u , v )$ and the $S -$ diameter by **diam** $\begin{array} { r } { ( H , S )   =   \operatorname* { m a x } _ { u , v \in V ( H ) } } \end{array}$ **dist** ${ } _ { H } ( u , v , S )$ **.** Therefore, $\mathbf { d i a m } ( H ) = \mathbf { d i a m } ( H , V )$ **For convenience, we often omit the subscript on relations if the context is clear and write** dist $( u , v , S )$

**We denote that a vertex u** reaches v in H by $u \quad { \leadsto } _ { H } \quad v .$ **,** and if $u   \leadsto _ { H } v$ and $v \leadsto _ { H } u .$ we simply write $u   \leftrightarrow _ { H }   v$ **and say u and v are** strongly-connected**. We also use** and $\rightleftarrows$ **without the subscript if the underlying graph H is clear from the context. We say that H is strongly-connected if for any** $u , v \: \in \: V ( H ) , u \: \rightleftarrows \: v .$ **We call the maximal subgraphs of H that are strongly-connected, the strongly-connected components (SCCs). We denote by Condensation(H) the** condensation **of H, that is the graph where all vertices in the same SCC in H are contracted. To distinguish we normally refer to the vertices in Condensation(H) as** nodes**. Each node in Condensation(H) corresponds to a vertex set in H. The node set of a condensation Condensation(H) forms a partition of** $V ( H )$ **. For convenience we define** the function Flatten(X) for a family of sets $X$ with Flatten $\textstyle ( X ) = \bigcup _ { x \in X } x$ **. This is useful when discussing condensations. Observe further that Condensation** $( H )$ **can be a multi-graph and might also contain self-loops. If we have an edge set** $E ^ { \prime }$ **with all endpoints in** $H .$ **, we let Condensation** $( H ) \cup E ^ { \prime }$ **be the multi-graph obtained by mapping the endpoints of each vertex** in $E ^ { \prime }$ **to their corresponding SCC node in Condensation(H) and adding the resulting edges to Condensation(H).**

Finally, for two partitions P and $P ^ { \prime }$ **of a set** $U ,$ **we say that partition P is a** melding **for a** partition $P ^ { \prime }$ if for every set $X \in P ^ { \prime }$ , there exists a set $Y \in P$ **with** $X \subseteq Y$ **. We also observe that** melding is transitive, thus if P is a melding for $P ^ { \prime }$ **a**nd $P ^ { \prime }$ a melding for $P ^ { \prime \prime }$ then $P$ is a melding for $P ^ { \prime \prime }$

## 3 Overview

**We now introduce the graph hierarchy maintained by our algorithm, followed by a high-level overview of our algorithm.**

**High-level overview of the hierarchy. Our hierarchy has levels 0 to** $\lfloor \lg n \rfloor + 1$ **and we** associate with each level i a subset $E _ { i }$ of the edges E. The sets $E _ { i }$ form a partition of $E ;$ we define the edges that go into each $E _ { i }$ later in the overview but point out that we maintain $E _ { \lfloor \lg n \rfloor + 1 } = \emptyset$ . We define a graph hierarchy $\hat { G } = \{ \hat { G } _ { 0 } , \hat { G } _ { 1 } , . . , \hat { G } _ { \lfloor \operatorname { l g } n \rfloor + 1 } \}$ such that each graph $\hat { G } _ { i }$ **i**s defined as

$$
\hat { G } _ { i } = \operatorname { C O N D E N S A T I O N } ( ( V , \bigcup _ { j < i } E _ { j } ) ) \cup E _ { i }
$$

**That is, each** $\hat { G } _ { i }$ **i**s the condensation of a subgraph of $G$ **with some additional edges. As** mentioned in the preliminary section, we refer to the elements of the set $\hat { V } _ { i } = V ( \hat { G } _ { i } )$ **as** nodes **to distinguish them from** vertices **in V . We use capital letters to denote nodes and small letters** to denote vertices. We let $X _ { i } ^ { v }$ **de**note the node in $\hat { V } _ { i }$ with $v \in X _ { i } ^ { v }$ Observe that each node X corresponds to a subset of vertices in V and that for any $i , ~ \hat { V } _ { i }$ **can in fact be seen as a** partition of $V$ . For Ĝ0 = Condensation $( ( V , \emptyset ) ) \cup E _ { 0 }$ **,** the set $\hat { V } _ { 0 }$ is a partition of singletons, i.e. $\hat { V } _ { 0 } = \{ \{ v \} | v \in V \}$ , and $X _ { 0 } ^ { v } = \{ v \}$ for each $v \in V$

Observe that because the sets $E _ { i }$ form a partition of E and $E _ { \lfloor \lg n \rfloor + 1 } = \emptyset$ , the top graph $\hat { G } _ { \lfloor \lg n \rfloor + 1 }$ **i**s simply defined as

$$
\hat { G } _ { \lfloor \operatorname { l g } n \rfloor + 1 } = \operatorname { C o N D E N S A T I O N } ( ( V , \bigcup _ { j < \lfloor \operatorname { l g } n \rfloor + 1 } E _ { j } ) ) \cup E _ { \lfloor \operatorname { l g } n \rfloor + 1 } = \operatorname { C o N D E N S A T I O N } ( ( V , E ) ) .
$$

Therefore, if we can maintain $\hat { G } _ { \lfloor \lg n \rfloor + 1 }$ **efficiently, we can answer queries on whether two** vertices $u , v \in V$ are in the same SCC in G by checking if $X _ { \lfloor \lg n \rfloor + 1 } ^ { u }$ is equal to $X _ { \lfloor \lg n \rfloor + 1 } ^ { v } .$

Let us offer some intuition for the hierarchy. The graph $\hat { G } _ { 0 }$ contains all the vertices of $G ,$ and all the edges of $E _ { 0 } \subseteq E$ By definition of Condensation(·), the nodes of $\hat { G } _ { 1 }$ precisely correspond to the SCCs of $\hat { G } _ { 0 } . \quad \hat { G } _ { 1 }$ also includes the edges $E _ { 0 }$ (though some of them are contracted into self-loops in Condensation $( ( V , E _ { 0 } ) ) )$ **,** as well as the additional edges in $E _ { 1 }$ These additional edges might lead to $\hat { G } _ { 1 }$ having larger SCCs than those of ${ \hat { G } } _ { 0 } ;$ **e**ach SCC in $\hat { G } _ { 1 }$ then corresponds to a node in $\hat { G } _ { 2 }$ . More generally, the nodes of $\hat { G } _ { i + 1 }$ are the SCCs of $\hat { G } _ { i }$

**As we move up the hierarchy, we add more and more edges to the graph, so the SCCs get larger and larger. Thus, each set** $\hat { V } _ { i }$ **i**s a melding for any $\hat { V } _ { j }$ **for** $j \leq i ;$ **that is for each** node $Y \in \hat { V } _ { j }$ there exists a set $X   \in   \hat { V } _ { i }$ **s**uch that $Y \subseteq X$ . We sometimes say we meld nodes $Y , Y ^ { \prime }   \in   \hat { V } _ { j }$ to $X   \in   \hat { V } _ { i }$ if $Y , Y ^ { \prime }   \subseteq   X$ **and** $j \: < \: i$ **. Additionally, we observe that for any SCC** $Y \subseteq { \hat { V } } _ { i }$ in $\hat { G } _ { i }$ , we meld the nodes in SCC Y to a node in $X \in \hat { V } _ { i + 1 }$ **, and X consists exactly of** the vertices contained in the nodes of Y . More formally, $X = \operatorname { F L A T T E N } ( Y )$

To maintain the SCCs in each graph $\hat { G } _ { i } ,$ **our algorithm employs a bottom-up approach.** At level $i + 1$ we want to maintain SCCs in the graph with all the edges in $\textstyle \bigcup _ { j \leq i + 1 } E _ { j }$ **, but** instead of doing so from scratch, we use the SCCs maintained at level $\hat { G } _ { i }$ **as a starting point.**

The SCCs in $\hat { G } _ { i }$ are precisely the SCCs in the graph with edge set $\textstyle \bigcup _ { j \leq i } E _ { j } ;$ **so to maintain the SCCs at level** $i + 1$ **, we only need to consider how the sliver of edges in** $E _ { i + 1 }$ **cause the SCCs** in $\hat { G } _ { i }$ to be melded into larger SCCs (which then become the nodes of $\hat { G } _ { i + 2 ) }$

If the adversary deletes an edge in $E _ { i }$ **,** all the graphs $\hat { G } _ { i - 1 }$ and below remain unchanged, as do the nodes of $\hat { G } _ { i }$ . But the deletion might split apart an SCC in $G _ { i } ,$ **which will in turn** cause a node of $\hat { G } _ { i + 1 }$ to split into multiple nodes. This split might then cause an SCC of $\hat { G } _ { i + 1 }$ **to split, which will further propagate up the hierarchy.**

**In addition to edge deletions caused by the adversary, our algorithm will sometimes move edges from** $E _ { i }$ **to** $E _ { i + 1 }$ **. Because the algorithm only moves edges** up **the hierarchy, each graph** $\hat { G } _ { i }$ **i**s only losing edges, so the update sequence remains decremental from the perspective of each $\hat { G } _ { i }$ **. We now give an overview of how our algorithm maintains the hierarchy efficiently.**

**ES-trees. A fundamental data structure that our algorithm employs is the ES-tree[ES81; HK95] that for a directed unweighted graph** $G   =   ( V , E )$ **undergoing edge deletions, and a distinguished source** $r   \in   V$ **maintains the distance dis** $\operatorname { t } _ { G } ( r , v )$ **for each** $v   \in   V$ **. In fact, the ES-tree maintains a shortest-path tree rooted at** $r .$ **We refer to this tree subsequently as ES out-tree. We call the ES in-tree rooted at** $r$ **the** shortest-path tree maintained by running the **ES-tree data structure on the graph** $G$ **with reversed edge set, i.e. the edge set where each edge** $( u , v ) \in E$ **appears in the form** $( v , u )$ **. We can maintain each in-tree and out-tree decrementally to depth** $\delta \; > \; 0$ **in time** $O ( | E | * \delta )$ **; that is we can maintain the distances** $\mathbf { d i s t } _ { G } ( r , v )$ **and** $\mathbf { d i s t } _ { G } ( v , r )$ **exactly until one of the distances dist** $\boldsymbol { \mathfrak { t } } _ { G } ( \boldsymbol { r } , \boldsymbol { v } )$ **or** $\mathbf { d i s t } _ { G } ( v , r )$ **exceeds δ.**

Maintaining SCCs with ES-trees. Consider again graph $\hat { G } _ { 0 }$ and let $X   \subseteq   \hat { V } _ { 0 }$ **be some** SCC in $\hat { G } _ { 0 }$ that we want to maintain. Let some node $X ^ { \prime }$ in $X$ **be chosen to be the** center **node** of the SCC (In the case of $\hat { G } _ { 0 }$ , the node $X ^ { \prime }$ is just a single-vertex set $\{ v \} )$ **. We then maintain** an ES in-tree and an ES out-tree from $X ^ { \prime }$ **that spans the nodes in X in the induced graph** $\hat { G } _ { 0 } [ X ]$ . We must maintain the trees up to distance diam $( \hat { G } _ { 0 } [ X ] )$ **, so the total update time is** $O ( | \widehat { E ( G _ { 0 } [ X ] ) } | * { \bf d i a m } ( \hat { G } _ { 0 } [ X ] ) )$

Now, consider an edge deletion to $\hat { G } _ { 0 }$ such that the ES in-tree or ES out-tree at $X ^ { \prime }$ **is no longer a spanning tree. Then, we detected that the SCC X has to be split into at least two** SCCs $X _ { 1 } , X _ { 2 } , . . , X _ { k }$ that are node-disjoint with $X = \textstyle \bigcup _ { i } X _ { i }$ . Then in each new SCC $X _ { i }$ **we choose a new center and initialize a new ES in-tree and ES out-tree.**

Exploiting small diameter. The above scheme clearly is quite efficient if $\mathbf { d i a m } ( \hat { G } _ { 0 } )$ **is very** small. Our goal is therefore to choose the edge set $E _ { 0 }$ in such a way that $\hat { G } _ { 0 }$ **contains only SCCs of small diameter. We therefore turn to some insights from [Che+16] and extract information** from the ES in-tree and out-tree to maintain small diameter. Their scheme fixes some $\delta > 0$ and if a set of nodes $Y \subseteq X$ **for some SCC X is at distance** $\Omega ( \delta )$ **from/to Center(X) due** to an edge deletion in $\hat { G } _ { 0 }$ , they find a node separator S of size O(min $\{ | Y | , | X \setminus Y | \}$ log $n / \delta )$ removing $S$ from $\hat { G } _ { 0 }$ **causes** $Y$ **and** $X \setminus Y$ **to no longer be in the same SCC. We use this** technique and remove edges incident to the node separator $S$ from $E _ { 0 }$ and therefore from $\hat { G } _ { 0 }$ **One subtle observation we want to stress at this point is that each node in the separator set** appears also as a single-vertex node in the graph $\hat { G } _ { 1 } ;$ this is because each separator node $\{ s \}$ for some $s \in V$ is not melded with any other node in $\hat { V } _ { 0 }$ , as it has no edges in $\hat { G } _ { 0 }$ **to or from any other node.**

For some carefully chosen $\delta = \Theta ( \log ^ { 2 } n )$ , we can maintain $\hat { G } _ { 0 }$ **such that at most half the** nodes in $\hat { V } _ { 0 }$ **become separator nodes at any point of the algorithm. This follows since each** separator set is small in comparison to the smaller side of the cut and since each node in $\hat { V } _ { 0 }$ can only be $O ( \log n )$ **times on the smaller side of a cut.**

**Reusing ES-trees. Let us now refine our approach to maintain the ES in-trees and ES out-trees and introduce a crucial ingredient devised by Roditty and Zwick[RZ08]. Instead of** picking an arbitrary center node $X ^ { \prime }$ from an SCC X with $X ^ { \prime }   \in   X$ **, we are going to pick a** vertex $r   \in   \operatorname { F L A T T E N } ( X )   \subseteq   V$ uniformly at random and run our ES in-tree and out-tree $\mathcal { E } _ { r }$ from the node $X _ { 0 } ^ { r }$ on the graph $\hat { G } _ { 0 }$ **. For each SCC X we denote the randomly chosen root r by Center(X). In order to improve the running time, we** reuse **ES-trees when the SCC X is split into SCCs** $X _ { 1 } , X _ { 2 } , . . , X _ { k }$ **, where we assume wlog that** $r \in \operatorname { F L A T T E N } ( X _ { 1 } )$ **, by removing the nodes in** $X _ { 2 } , . . , X _ { k }$ **from** $\mathcal { E } _ { r }$ **and setting Center** $( X _ { 1 } ) = r$ **. Thus, we only need to initialize a new ES-tree for the SCC** $X _ { 2 } , . . , X _ { k }$ **Using this technique, we can show that each node is expected to participate in** $O ( \log n )$ **ES-trees over the entire course of the algorithm, since we expect that if a SCC X breaks into SCCs** $X _ { 1 } , X _ { 2 } , . . , X _ { k }$ **then we either have that every SCC** $X _ { i }$ **i**s of at most half the size of X, or with probability at least $1 / 2$ **that** $X _ { 1 }$ **is the new SCC that contains at least half the vertices, i.e. that the random root is containing in the largest part of the graph. Since the ES-trees work on induced graphs with disjoint node sets, we can** therefore conclude that the total update time for all ES-trees is $O ( m \operatorname { l o g } n * { \bf d i a m } ( \hat { G } _ { 0 } ) )$

**We point out that using the ES in-trees and out-trees to detect node separators as described above complicates the analysis of the technique by Roditty and Zwick[RZ08] but a clever proof presented in [Che+16] shows that the technique can still be applied. In our paper, we present a proof that can even deal with some additional complications and that is slightly simpler.**

**A contrast to the algorithm of Chechik et al [Che+16]. Other than our hierarchy, the overview we have given so far largely comes from the algorithm of Chechik et al [Che+16]. However, their algorithm does not use a hierarchy of graphs. Instead, they show that for any graph G, one can find (and maintain) a node separator S of size** $\tilde { O } ( n / \delta )$ **s**uch that all SCCs **in** $G$ **have diameter at most δ. They can then use ES-trees with random sources to maintain the SCCs in** $G \setminus S$ **in total update time** $\tilde { O } ( m \delta )$ **. This leaves them with the task of computing how the vertices in S might meld some of the SCCs in** $G \setminus S$ **. They are able to do this in total update time** $\tilde { O } ( m | S | ) = \tilde { O } ( m n / \delta )$ **by using an entirely different technique of [Łąc13]. Setting** $\delta = \tilde { O } ( \sqrt { n } )$ **, they achieve the optimal trade-off between the two techniques: total update time** $\tilde { O } ( m \sqrt { n } )$ **in expectation.**

**We achieve our** $\tilde { O } ( m )$ **total update time by entirely avoiding the technique of** $\mathrm { [ L a c 1 3 ] }$ **for separately handling a small set of separator nodes, and instead using the graph hierarchy** described above, where at each level we set δ to be polylog rather than ${ \tilde { O } } ( { \sqrt { n } } )$

**We note that while our starting point is the same as [Che+16], using a hierarchy of separators forces us to take a different perspective on the function of a separator set. The reason is that it is simply not possible to ensure that at each level of the hierarchy, all SCCs have small diameter. To overcome this, we instead aim for separator sets that decompose the graph into SCCs that are small with respect to a different notion of distance. The rest of the overview briefly sketches this new perspective, while sweeping many additional technical challenges under the rug.**

Refining the hierarchy. So far, we only discussed how to maintain $\hat { G } _ { 0 }$ **efficiently by deleting** many edges from $E _ { 0 }$ and hence ensuring that SCCs in $\hat { G } _ { 0 }$ **have small diameter. To discuss our** bottom-up approach, let us define our graphs $\hat { G } _ { i }$ **more precisely.**

We maintain a separator hierarchy $\mathcal { S } = \{ S _ { 0 } , S _ { 1 } , . . , S _ { \lfloor \lg n \rfloor + 2 } \}$ where $\hat { V } _ { 0 }   =   S _ { 0 }   \supseteq   S _ { 1 }   \supseteq   . .   \supseteq$ $S _ { \lfloor \lg n \rfloor + 1 } = S _ { \lfloor \lg n \rfloor + 2 } = \emptyset$ , with $| S _ { i } | \leq n / 2 ^ { i }$ , for all $i \in [ 0 , \lfloor \bar { \lg n } \rfloor + 2 ]$ (see below that for technical reasons we need to define $S _ { \lfloor \lg n \rfloor + 2 }$ to define $\hat { G } _ { \lfloor \lg n \rfloor + 1 } )$ . Each set $S _ { i }$ **i**s a set of single-vertex **nodes – i.e. nodes of the form** $\{ \bar { v } \} -$ **that is monotonically increasing over time.**

**We can now more precisely define each edge set** $E _ { i } { = } E ( \operatorname { F L A T T E N } ( S _ { i } \setminus S _ { i + 1 } ) )$ **. To avoid clutter, we abuse notation slightly referring henceforth to Flatten(X) simply as X if X is a set of singleton sets and the context is clear. We therefore obtain**

$$
\hat { G } _ { i } = \operatorname { C o N D E N S A T I O N } ( ( V , \bigcup _ { j < i } E _ { j } ) ) \cup E _ { i } = \operatorname { C o N D E N S A T I O N } ( G \setminus E ( S _ { i } ) ) \cup E ( S _ { i } \setminus S _ { i + 1 } ) ) .
$$

In particular, note that $\hat { G } _ { i }$ **contains all the edges of** $G$ **e**xcept those in $E ( S _ { i + 1 } ) ;$ as we move up to level $\hat { G } _ { i + 1 }$ **, we add the edges incident to** $S _ { i + 1 } \setminus S _ { i + 2 }$ **. Note that if** $s \in S _ { i } \setminus S _ { i + 1 }$ **, and our algorithm then adds s to** $S _ { i + 1 }$ **, this will remove all edges incident to s from** $E _ { i }$ **and add them to** $E _ { i + 1 }$ **. Thus the fact that the sets** $S _ { i }$ **used by the algorithm are monotonically increasing implies the desired property that edges only move up the hierarchy (remember that we add** more vertices to $S _ { i }$ due to new separators found on level $i - 1 )$

**At a high-level, the idea of the hierarchy is as follows. Focusing on a level i, when the** “distances” in some SCC of $\hat { G } _ { i }$ **get too large (for a notion of distance defined below), the algorithm will add a carefully chosen set of separator nodes** $s _ { 1 } , s _ { 2 } , . .$ **. in** $S _ { i }$ **to** $S _ { i + 1 }$ **. By definition** of our hierarchy, this will remove the edges incident to the $s _ { i }$ from $\hat { G } _ { i }$ **, thus causing the SCCs** of $\hat { G } _ { i }$ **to decompose into smaller SCCs with more manageable “distances”. We note that our** algorithm always maintains the invariant that nodes added to $S _ { i + 1 }$ were previously in $S _ { i } ,$ **which from the definition of our hierarchy, ensures that at all times the separator nodes in** $S _ { i + 1 }$ **are** single-vertex nodes in $\hat { V } _ { i + 1 } ;$ this is because the nodes of $\hat { V } _ { i + 1 }$ are the SCCs of $\hat { G } _ { i }$ , and $\hat { G } _ { i }$ contains no edges incident to $S _ { i + 1 }$

**Exploiting S-distances. For our algorithm, classic ES-trees are only useful to maintain** SCCs in ${ \hat { G } } _ { 0 } ;$ **in order to handle levels** $i > 0$ **we develop a new generalization of ES-trees that** use a different notion of distance. This enables us to detect when SCCs are split in graphs $\hat { G } _ { i }$ and to find separator nodes in $\hat { G } _ { i }$ **as discussed above more efficiently.**

**Our generalized ES-tree (GES-tree) can be seen as a combination of the classic ES-trees[ES81] and a data structure by Italiano[Ita88] that maintains reachability from a distinguished source** in a directed acyclic graph (DAG), and which can be implemented in total update time $O ( m )$

**Let S be some feedback vertex set in a graph** $G = ( V , E )$ **; that is, every cycle in G contains a vertex in S. Then our GES-tree can maintain S-distances and a corresponding shortest-path** tree up to S-distance $\delta > 0$ from a distinguished source $X _ { i } ^ { r }$ for some $r \in V$ **in the graph G. (See Section 2 for the definition of S-distances.) This data structure can be implemented to take** $O ( m \delta )$ **total update time.**

Maintaining the SCCs in $\hat { G } _ { i }$ . Let us focus on maintaining SCCs in $\hat { G } _ { i } = \operatorname { C O N D E N S A T I O N } ( G \backslash$ $E ( S _ { i } ) ) \cup E ( S _ { i } \setminus S _ { i + 1 } )$ . Since the condensation of any graph forms a DAG, every cycle in $\hat { G } _ { i }$ contains at least one edge from the set $E ( S _ { i } \setminus S _ { i + 1 } )$ . Since $E ( S _ { i } \setminus S _ { i + 1 } )$ is a set of edges that is incident to $S _ { i } .$ , we have that $S _ { i }$ forms a feedback node set of $\hat { G } _ { i }$ . Now consider the scheme described in the paragraphs above, but instead of running an ES in-tree and out-tree from each center Center $( X )$ for some SCC X, we run a GES in-tree and out-tree on $\hat { G } _ { i } [ X ]$ that maintains the S<sub>i</sub>-distances to depth δ. Using this GES, whenever a set $Y \subseteq X$ of nodes has S<sub>i</sub>-distance $\Omega ( \delta )$ , we show that we can find a separator $S$ of size $O ( \operatorname* { m i n } \{ | S _ { i } \cap Y | , | S _ { i } \cap ( X \setminus Y ) | \}$ log $n / \delta )$ that only consists of nodes that are in $\{ \{ s \} | s \in S _ { i } \}$ ; we then add the elements of set $S$ to the set $S _ { i + 1 }$ , and we also remove the nodes Y from the GES-tree, analogously to our discussion of regular ES-trees above. Note that adding S to $S _ { i + 1 }$ removes the edges $E ( S )$ from ${ \hat { G } } _ { i } ;$ since we chose S to be a separator, this causes $Y$ and $X \setminus Y$ to no longer be part of the same SCC in $\hat { G } _ { i }$ . Thus, to maintain the hierarchy, we must then split nodes in $\hat { G } _ { i + 1 }$ into multiple nodes corresponding to the new SCCs in $\hat { G } _ { i } { : ~ } X \setminus ( Y \cup S )$ $Y \setminus S$ and every single-vertex set in S (Y might not form a SCC but we then further decompose it after we handled the node split). This might cause some self-loops in $\hat { G } _ { i + 1 }$ to become edges between the newly inserted nodes (resulting from the split) and needs to be handled carefully to embed the new nodes in the GES-trees maintained upon the SCC in $\hat { G } _ { i + 1 }$ that X is part of. Observe that this does not result in edge insertions but only remaps the endpoints of edges. Further observe that splitting nodes can only increase $S _ { i + 1 }$ **-**distance since when they were still contracted their distance from **the center was equivalent. Since** $S _ { i + }$ 1**-distance still might increase, the update to might trigger** further changes in the graph $\hat { G } _ { i + 1 }$

Thus, overall, we ensure that all SCCs in $\hat { G } _ { i }$ **have** $S _ { i }$ **-diameter at most** $O ( \delta )$ **, and can hence be efficiently maintained by GES-trees. In particular, we show that whenever an SCC exceeds diameter** $\delta ,$ **we can, by moving a carefully chosen set of nodes in** $S _ { i }$ **to** $S _ { i + 1 }$ **, remove a** corresponding set of edges in $\hat { \dot { G } } _ { i }$ **, which breaks the large-Si-diameter SCC into SCCs of smaller S**<strong><sub>i</sub></strong>**-diameter.**

**Bounding the total update time. Finally, let us sketch how to obtain the total expected running time** $O ( m \log ^ { 4 } n )$ **. We already discussed how by using random sources in GES-trees (analogously to the same strategy for ES-trees), we ensure that each node is expected to be in** $O ( \log n )$ **GES-trees maintained to depth** $\delta = O ( \log ^ { 2 } n )$ **. Each such GES-tree is maintained in total update time** $O ( m \delta )   =   O ( m \log ^ { 2 } n )$ **, so we have** $O ( m \log ^ { 3 } n )$ **total expected update time for each level, and since we have** $O ( \log n )$ **levels, we obtain total expected update time** $O ( m \log ^ { 4 } n )$ **We point out that we have not included the time to compute the separators in our running time analysis; indeed, computing separators efficiently is one of the major** **challenges to building our hierarchy. Since implementing these subprocedures efficiently is rather technical and cumbersome, we omit their description from the overview but refer to section 6 for a detailed discussion.**

## 4 Generalized ES-trees

**Even and Shiloach[ES81] devised a data structure commonly referred to as ES-trees that given a vertex** $r \in V$ **in a graph** $G = ( V , E )$ **undergoing edge deletions maintains the shortest-path tree from r to depth δ in total update time** $O ( m \delta )$ **such that the distance dist** $\boldsymbol { \mathfrak { t } } _ { G } ( \boldsymbol { r } , \boldsymbol { v } )$ **of any vertex** $v \in V$ **can be obtained in constant time. Henzinger and King[HK95] later observed that the ES-tree can be adapted to maintain the shortest-path tree in directed graphs.**

**For our algorithm, we devise a new version of the ES-trees that maintains the shortestpath tree with regard to S-distances. We show that if S is a** feedback vertex set **for** $G .$ **, that is a set such that every cycle in** $G$ **contains at least one vertex in** $S ,$ **then the data structure requires only** $O ( m \delta )$ **total update time. Our fundamental idea is to combine classic ES-trees with techniques to maintain Single-Source Reachability in DAGs which can be implemented in linear time in the number of edges[Ita88]. Since dis** $\mathbf { t } _ { G } ( r , v ) = \mathbf { d i s t } _ { G } ( r , v , V )$ **and** $V$ **is a trivial feedback vertex set, we have that our data structure generalizes the classic ES-tree. Since the empty set is a feedback vertex set for DAGs, our data structure also matches the time complexity of Italiano’s data structure. We define the interface formally below.**

**Definition 4.1.** Let $G = ( V , E )$ be a graph and S a feedback vertex set for $G ,   r \in V$ and $\delta > 0$ We define a generalized ES-tree $\mathcal { E } _ { r } ~ \left( G E S \right)$ to be a data structure that supports the following operations:

• **InitGES** $( r , G , S , \delta )$ : Sets the parameters for our data structure. We initialize the data structure and return the GES.

• **Distance(r, v)**: **∀v ∈ V** , if **dis** $\mathbf { t } _ { G } ( r , v , S ) \leq \delta$ , **E**<strong><sub>r</sub></strong> reports **dis** $\mathbf { t } _ { G } ( r , v , S )$ , otherwise ∞.

• **Distance(v, r)**: **∀v ∈ V** , $\mathit { i f }   \mathbf { d i s t } _ { G } ( v , r , S ) \leq \delta ,$ **E**<strong><sub>r</sub></strong> reports **dis** $\mathbf { t } _ { G } ( v , r , S )$ , otherwise ∞.

• **Delete(u, v)**: Sets $E \gets E \setminus \{ ( u , v ) \}$

• **Delete(V**′): For $V ^ { \prime } \subseteq V _ { \iota }$ , sets $V   \leftarrow   V \setminus V ^ { \prime }$ , i.e. removes the vertices in $V ^ { \prime }$ and all incident edges from the graph G.

• **GetUnreachableVertex()**: Returns a vertex $v \in V$ with max $\{ \mathbf { d i s t } _ { G } ( r , v , S )$ , dist $\iota _ { G } ( v , r , S ) \} >$ $\delta \textit { o r } \bot \textit { i f }$ no such vertex exists.

**Lemma 4.2.** The $G E S   \mathcal { E } _ { r }$ as described in definition 4.1 can be implemented with total initialization and update time $O ( m \delta )$ and requires worst-case time $O ( 1 )$ for each operation **Distance(·)** and **GetUnreachableVertex()**.

**We defer the full prove to the appendix B but sketch the proof idea.**

Proof. **(sketch) Consider a classic ES-tree with each edge weight** $w ( u , v )$ **of an edge** $( u , v )$ **in** $E _ { o u t } ( S )$ **s**et to 1 and all other edges of weight 0. Then, the classic ES-tree analysis maintains **with each vertex** $v \in V$ **the distance level** $l ( v )$ **that expresses the current distance from s to v.** We also have a shortest-path tree $T .$ where the path in the tree from s to v is of weight $l ( v )$ Since $T$ is a shortest-path tree, we also have that for every edge $( u , v ) \in E ,   l ( v ) \leq l ( u ) + w ( u , v )$ Now, consider the deletion of an edge $( u , v )$ from G that removes an edge that was in $T .$ **.** To certify that the level $l ( v )$ does not have to be increased, we scan the in-going edges at v and try to find an edge $( u ^ { \prime } , v ) \in E$ such that $l ( v ) = l ( u ^ { \prime } ) + w ( u ^ { \prime } , v )$ **.** On finding this edge, $( u ^ { \prime } , v )$ is added to $T .$ . The problem is that if we allow 0-weight cycles, the edge $( u ^ { \prime } , v )$ that we use to reconnect v might come from a $u ^ { \prime }$ that was a descendant of $v$ in $T .$ This will break the algorithm, as it disconnects v from s in $T .$ But we show that this bad case cannot occur because S is assumed to be a feedback vertex set, so at least one of the vertices on the cycle must be in $S$ **and** therefore the out-going edge of this vertex must have weight 1 contradicting **that there exists any 0-weight cycle. The rest of the analysis follows closely the classic ES-tree analysis.** □

**To ease the description of our SCC algorithm, we tweak our GES implementation to work on** the multi-graphs $\hat { G } _ { i }$ . We still root the GES at a vertex $r \in V$ , but maintain the tree in $\hat { G } _ { i }$ at $X _ { i } ^ { r }$ The additional operations and their running time are described in the following lemma whose proof is straight-forward and therefore deferred to appendix C. Note that we now deal with nodes rather than vertices which makes the definition of S-distances ambitious (consider for example a node containing two vertices in S). For this reason, we require $S \subseteq \{ \{ v \} | v \in V \}   \cap   \hat { V }$ **i**n the lemma below, **i.**e. that the nodes containing vertices **in** $S$ **are single-vertex nodes. But as discussed in the paragraph “Refining the hierarchy" in the overview, our hierarchy ensures that every separator node** $X \in S _ { i }$ **i**s always just a single-vertex node in $\hat { G } _ { i }$ **. Thus this constraint can be satisfied by our hierarchy.**

**Lemma 4.3.** Say we are given a partition $\hat { V }$ of a universe V and the graph $\hat { G } = ( \hat { V } , E )$ , a feedback node set $S \subseteq \{ \{ v \} | v \in V \} \cap { \hat { V } }$ , a distinguished vertex $r \in V$ , and a positive integer δ. Then, we can run a $G E S   \mathcal { E } _ { r }$ as in definition $4 . I$ on $\hat { G }$ in time $O ( m \delta + \textstyle \sum _ { X \in { \hat { V } } } E ( X )$ **log X)** supporting the additional operations:

• **SplitNode(X)**: the input is a set of vertices X contained in node $Y   \in   \hat { V }$ , such that either $E   \cap   \left( X \times Y \setminus X \right)$ or $E   \cap   \left( Y   \backslash   X   \times   X \right)$ is an empty set, which implies $X \not \sim _ { \hat { G } \setminus S } Y \backslash X$ We remove the node $Y$ in $\hat { V }$ and add node X and **Y \ X** to $\hat { V }$

• Augment $( S ^ { \prime } )$ : This procedure adds the nodes in $S ^ { \prime }$ to the feedback vertex set S. Formally, the input is a set of single-vertex sets $S ^ { \prime } \subseteq \{ \{ v \} | v \in V \} \cap { \hat { V } }$ . Augment $( S ^ { \prime } )$ then adds every $s \in S ^ { \prime }$ to $S .$

**We point out that we enforce the properties on the set X in the operation SplitNode(X) in order to ensure that the set** $S$ **remains a feedback node set at all times.**

## 5 Initializing the the graph hierarchy $\hat { \mathcal { G } }$

**We assume henceforth that the graph G initially is strongly-connected. If the graph is not strongly-connected, we can run Tarjan’s algorithm[Tar72] in** $O ( m + n )$ **time to find the SCCs of G and run our algorithm on each SCC separately.**

<div class="docvortex-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: Preprocessing $( G , \delta )$
Input: A strongly-connected graph $\overline { { G } } = ( V , E ) .$ and a parameter $\delta &gt; 0 .$
Output: A hierarchy of sets $\mathcal { S } = \{ S _ { 0 } , S _ { 1 } , . . , S _ { \lfloor \operatorname { l g } n \rfloor + 2 } \}$ and graphs
$\hat { \mathcal { G } } = \{ \hat { G } _ { 0 } , \hat { G } _ { 1 } , . . , \hat { G } _ { \lfloor \operatorname { l g } n \rfloor + 1 } \}$ as described in section 3. Further, each SCC X in
$\hat { G } _ { i }$ for $i \leq \lfloor \lg n \rfloor + 2 ,$ has a center Center(X) such that for any $y \in X$
$\mathbf { d i s t } _ { \hat { G } _ { i } } ( \operatorname { C E N T E R } ( X ) , y , S _ { i } ) \leq \delta / 2$ and dis $\mathsf { t } _ { \hat { G } _ { i } } ( y ,$ Center $( X ) , S _ { i } ) \leq \delta / 2 .$
1 $S _ { 0 } \leftarrow V$
2 $\hat { V } _ { 0 } \leftarrow \{ \{ v \} | v \in V \}$
3 $\hat { G } _ { 0 } \gets ( \hat { V } _ { 0 } , E )$
4 for $i = 0$ to ⌊lg n⌋ do
/* Find separator $S _ { S e p }$ such that no two vertices in the same SCC in $\hat { G } _ { i }$
have $S _ { i } { \mathrm { - d i } }$ stance $\geq \delta / 2$ P is the collection of these SCCs. * /
5 $( S _ { S e p } , P ) \leftarrow \operatorname { S P L I T } ( \hat { G } _ { i } , S _ { i } , \delta / 2 )$
6 $S _ { i + 1 } \gets S _ { S e p }$
7 InitNewPartition $( P , i , \delta )$
$/ *$ Initialize the graph $\hat { G } _ { i + 1 }$ */
8 $\hat { V } _ { i + 1 } \leftarrow P$
9 $\hat { G } _ { i + 1 } \gets ( \hat { V } _ { i + 1 } , E )$
10 $S _ { \lfloor \lg n \rfloor + 2 } \leftarrow \emptyset$
</div>

**Our procedure to initialize our data structure is presented in pseudo-code in algorithm 1.** We first initialize the level 0 where $\hat { G } _ { 0 }$ **is simply G with the vertex set V mapped to the set of singletons of elements in V .**

**Let us now focus on an iteration i. Observe that the graph** $\hat { G } _ { i }$ **i**nitially has all edges in $E$ (by initializing each $\hat { G } _ { i }$ **in** line 3 or line 9). Our goal is then to ensure that all SCCs in $\hat { G } _ { i }$ are of small Si-diameter at the cost of removing some of the edges from $\hat { G } _ { i }$ **. Invoking the** procedure $\operatorname { S P L I T } ( \hat { G } _ { i } , S _ { i } , \delta / 2 )$ **provides us with a set of separator nodes** $S _ { S e p }$ **whose removal** from $\hat { G } _ { i }$ **e**nsure that the $S _ { i }$ diameter of all remaining SCCs is at most δ. The set P is the collection of all these SCCs, i.e. the collection of the SCCs in $\hat { G } _ { i } \setminus E ( S _ { S e p } )$

Lemma 5.1 below describes in detail the properties satisfied by the procedure $\operatorname { S P L I T } ( \hat { G } _ { i } , S _ { i } , \delta / 2 )$ In particular, besides the properties ensuring small $S _ { i ^ { * } }$ **-**diameter in the graph $\hat { G } _ { i } \backslash E ( S _ { S e p } )$ (prop**erties 1 and 2), the procedure also gives an upper bound on the number of separator vertices** (property 3). Setting $\delta   =   6 4 \lg ^ { 2 } n ,$ , clearly implies that $| S _ { S e p } |   \leq   | S _ { i } | / 2$ **and ensures running** time $O ( m \log ^ { 3 } n )$

Lemma 5.1. Split $( \hat { G } _ { i } , S _ { i } , \delta / 2 )$ returns a tuple $( S _ { S e p } , P )$ where P is a partition of the node set $\hat { V } _ { i }$ such that

1. for $X \in P ,$ , and nodes $u , v \in X$ we have dist $\mathfrak { t } _ { G \setminus E ( S _ { S e p } ) } ( u , v , S ) \leq \delta / 2$ , and

2. for distinct $X , Y \in P ,$ , with nodes $u \in X$ and $v \in Y ,   u \not\sim_{G \setminus E(S_{S e p})} v,$ and

$$
\textstyle | S _ { S e p } | \leq \frac { 3 2 \operatorname { l g } ^ { 2 } n } { \delta } | S _ { i } | .
$$

The algorithm runs in time $O \left( \delta m \lg n \right)$

We then set $S _ { i + 1 } = S _ { S e p }$ which implicitly removes the edges $E ( S _ { i + 1 } )$ from the graph $\hat { G } _ { i }$ We then invoke the procedure InitNewPartition $( P , i , \delta )$ , that is presented in algorithm 2. The procedure initializes for each $X \in P$ that corresponds to an SCC in $\hat { G } _ { i }$ the GES-tree from a vertex $r \in \operatorname { F L A T T E N } ( X )$ chosen uniformly at random on the induced graph $\hat { G } _ { i } [ X ]$ **.** Observe **that we are not explicitly keeping track of the edge set** $E _ { i }$ **but further remove edges implicitly** by only maintaining the induced subgraphs of $\hat { G } _ { i }$ **t**hat form SCCs. A small detail we want **to point out is that each separator node** $X \in S _ { S e p }$ **also forms its own single-node set in the partition P.**

<div class="docvortex-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2: InitNewPartition $( P , i , \delta )$
Input: A partition of a subset of the nodes $\overline { { V } } ,$ and the level i in the hierarchy.
Result: Initializes a new ES-tree for each set in the partition on the induced subgraph
${ \hat { G } } _ { i } .$
1 foreach $X \in P$ do
2 Let r be a vertex picked from Flatten(X) uniformly at random.
3 Center(X) ← r
/* Init a generalized ES-tree from Center(X) to depth $\delta$ * /
4 $\mathcal { E } _ { r } ^ { i } \leftarrow \operatorname { I N I T G E S } ( \operatorname { C E N T E R } ( X ) , \hat { G } _ { i } [ X ] , S _ { i } , \delta )$
</div>

On returning to algorithm 1, we are left with initializing the graph $\hat { G } _ { i + 1 }$ **. Therefore, we** simply set $\hat { V } _ { i + 1 }$ **to** $P$ **and use again all edges E. Finally, we initialize** $S _ { \lfloor \lg n \rfloor + 2 }$ **to the empty set which remains unchanged throughout the entire course of the algorithm.**

**Let us briefly sketch the analysis of the algorithm which is more carefully analyzed in** subsequent sections. Using again $\delta = 6 4   \mathrm { l g } ^ { 2 }$ n and lemma 5.1, we ensure that $| S _ { i + 1 } | \leq | S _ { i } | / 2$ thus $| S _ { i } | \leq n / 2 ^ { i }$ for all levels i. The running time of executing the Split(·) procedure ⌊lg $n \rfloor + 1$ **time**s incurs running time $O ( m \log ^ { 4 } n )$ and initializing the GES-trees takes at most $O ( m \delta )$ time on each level therefore incurring running time $O ( m \log ^ { 3 } n )$

## 6 Finding Separators

**Before we describe how to update the data structure after an edge deletion, we want to explain how to find good separators since it is crucial for our update procedure. We then show how** **to obtain an efficient implementation of the procedure** $\mathrm { S P L I T } ( \cdot )$ **that is the core procedure in the initialization.**

**Indeed, the separator properties that we want to show are essentially reflected in the properties of lemma 5.1. For simplicity, we describe the separator procedures on simple graphs instead of our graphs** ${ \hat { G } } _ { i } ;$ **i**t is easy to translate these procedures to our multi-graphs $\hat { G } _ { i }$ **because the separator procedures are not dynamic; they are only ever invoked on a fixed graph, and so we do not have to worry about node splitting and the like.**

**To gain some intuition for the technical statement of our separator properties stated in lemma 6.1, consider that we are given a graph** $G   =   ( V , E )$ **, a** subset S of the vertices V , a **vertex** $r \in V$ **and a depth d. Our goal is to find a separator** $S _ { S e p } \subseteq S$ **, such that every vertex in the graph** $G \setminus S _ { S e p }$ **is either at S-distance at most d from** $r \_ o r$ **cannot be reached from r, i.e. is separated from r.**

**We let henceforth** $V _ { S e p } \subseteq V$ **denote the set of vertices that are still reachable from r in** $G \setminus S _ { S e p }$ **(in particular there is no vertex** $S _ { S e p }$ **contained in** $V _ { S e p }$ **and** $r \in V _ { S e p } )$ **. Then, a natural side condition for separators is to require the set** $S _ { S e p }$ **to be small in comparison to the smaller** side of the cut, i.e. small in comparison to min $\{ | V _ { S e p } | , | V \setminus ( V _ { S e p } \cup S _ { S e p } ) | \}$

**Since we are concerned with S-distances, we aim for a more general guarantee: we want the set** $S _ { S e p }$ **to be small in comparison to the number of S vertices on any side of the cut, i.e. small in comparison to min** $\{ | V _ { S e p } \cap S | , | ( V \setminus ( V _ { S e p } \cup S _ { S e p } ) ) \cap S | \}$ **. This is expressed in property 3 of the lemma.**

**Lemma 6.1 (Balanced Separator).** There exists a procedure OutSeparator $. ( r , G , S , d )$ (analogously InSeparator $( r , G , S , d ) )$ where $G = ( V , E )$ is a graph, $r \in V$ a root vertex, $S \subseteq V$ and d a positive integer. The procedure computes a tuple $( S _ { S e p } , V _ { S e p } )$ such that

$$
\mathit { 1 . } \quad \mathit { S } _ { \mathit { S e p } } \subseteq \mathit { S } , \quad \mathit { V } _ { \mathit { S e p } } \subseteq \mathit { V } , \quad \mathit { S } _ { \mathit { S e p } } \cap \mathit { V } _ { \mathit { S e p } } = \emptyset , \quad \mathit { r } \in \mathit { V } _ { \mathit { S e p } } ,
$$

2. $\forall v \in V _ { { S e p } } \cup S _ { { s e p } } ,$ we have **dis** $\mathbf { t } _ { G } ( r , v , S ) \leq d$ (analogously **dis** $\mathtt { t } _ { G } ( v , r , S ) \leq d$ for **InSeparator** $( r , G , S , d ) )$ ,

3.

$$
| S _ { S e p } | \leq \frac { \operatorname* { m i n } \{ | V _ { S e p } \cap S | , | ( V \setminus ( S _ { S e p } \cup V _ { S e p } ) ) \cap S | \} 2 \operatorname { l o g } n } { d } ,
$$

and

4. for any $x \; \in \; V _ { S e p }$ and $y \; \in \; V \backslash ( S _ { S e p } \cup V _ { S e p } )$ , we have **u** $\not \sim _ { G \setminus E ( S _ { S e p } ) }$ v (analogously $v \not \sim _ { G \setminus E ( S _ { S e p } ) }$ u for InSeparator $. ( r , G , S , d ) )$

The running time of both **OutSeparator(·)** and **InSeparator(·)** can be bounded by $O ( E ( V _ { S e p } ) )$

**Again, we defer the proof of the lemma 6.1 to the appendix D, but sketch the main proof idea.**

Proof. **To implement procedure** $\operatorname { O U T S E P A R A T O R } ( r , G , S , d )$ **, we start by computing a BFS at r. Here, we assign edges in** $E _ { o u t } ( S )$ **again weight 1 and all other edges weight 0 and say a layer consists of all vertices that are at same distance from r. To find the first layer, we can use the graph** $G \setminus E _ { o u t } ( S )$ **and run a normal BFS from r and all vertices reached form the first layer**

$L _ { 0 }$ **We can then add for each edge** $( u , v ) \in E _ { o u t } ( S )$ **with** $u \in L _ { 0 }$ **t**he vertex v to $L _ { 1 }$ if it is not already in $L _ { 0 }$ . We can then contract all vertices visited so far into a single vertex $r ^ { \prime }$ **and repeat the procedure described for the initial root r. It is straight-forward to see that the vertices of a layer that are also in S form a separator of the graph. To obtain a separator that is small in comparison to** $| V _ { S e p } \cap S |$ **,** we add each of the layers 0 to $d / 2$ one after another to our set $V _ { S e p } ,$ and output the index i of the first layer that grows the set of S-vertices in $V _ { S e p }$ **by factor less** than $\textstyle ( 1 + { \frac { 2 \log n } { d } } )$ . We then set $S _ { S e p }$ to be the vertices in S that are in layer i. If the separator is not small in comparison to $| ( V \setminus \dot { ( } S _ { S e p } \cup V _ { S e p } ) ) \cap S |$ , we grow more layers and output the first **index of a layer such that the separator is small in comparison to** $| ( V \setminus ( S _ { S e p } \cup V _ { S e p } ) ) \cap S |$ **. This layer must exist and is also small in comparison to** $| V _ { S e p } \cap S |$ **. Because we find our separator vertices** $S _ { S e p }$ **using a BFS from r, a useful property of our separator is that all the vertices in** $S _ { S e p }$ **and** $V _ { S e p }$ **are within bounded distance from r.**

**Finally, we can ensure that the running time of the procedure is linear in the size of the set** $E ( V _ { S e p } )$ **, since these are the edges that were explored by the BFS from root r.** □

**Let us now discuss the procedure** $\operatorname { S P L I T } ( G , S , d )$ **that we already encountered in section 5 and whose pseudo-code is given in algorithm 3. Recall that the procedure computes a tuple** $( S _ { S p l i t } , P )$ **such that the graph** $G \setminus E ( S _ { S p l i t } )$ **contains no SCC with S-diameter larger d and** where P is the collection of all SCCs in the graph $G \setminus E ( S _ { S p l i t } )$

**Let us sketch the implementation of the procedure** $\operatorname { S P L I T } ( G , S , d )$ **We first pick an arbitrary** vertex and invoke the procedures OutSeparator $\mathfrak { i } ( r , G ^ { \prime } , S , d / 4 )$ and InSeparator $( r , G ^ { \prime } , S , d / 4 )$ **to run in parallel, that is the operations of the two procedures are interleaved during the execution. If one of these subprocedures returns and presents a separator tuple** $( S _ { S e p } , V _ { S e p } )$ **, the** other procedure is aborted and the tuple $( S _ { S e p } , V _ { S e p } )$ is returned. If $| V _ { S e p } |   \leq   { \textstyle \frac { 2 } { 3 } } | \widetilde { V } |$ **, then we conclude that the separator function only visited a small part of the graph. Therefore, we use** the separator subsequently, but denote the tuple henceforth as $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } )$ **Otherwise, we decide the separator is not useful for our purposes. We therefore return to the subprocedure we previously aborted and continue its execution. We then continue with the returned tuple** $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } )$

**From there on, there are two possible scenarios. The first scenario is that the subprocedure** producing $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } )$ **has visited a rather small fraction of the vertices in V (line 8); in** this case, we have pruned away a small number of vertices $V _ { S e p } ^ { \prime }$ **while only spending time** proportional to the smaller side of the cut, so we can simply recurse on $V _ { S e p } ^ { \prime }$ **. We also have to continue pruning away vertices from the original set** $V ,$ **until we have either removed all vertices from G by finding these separators and recursing, or until we enter the else-case (line 13).**

**The else-case in line 13 is the second possible scenario: note that in this case we must have entered the else-case in line 6 and had both the InSeparator(·)** and **OutSeparator(·) explore the large side of the cut. Thus we cannot afford to simply recurse on the smaller side** of the cut $V \setminus V _ { s e p } ^ { \prime } ,$ as we have already spent time $| V _ { s e p } ^ { \prime } | > | V \setminus V _ { s e p } ^ { \prime } |$ **. Thus, for this case we use a different approach. We observe that because we entered the else-case in line 6 and since we** entered the else-case 13, we must have had that $| V _ { S e p } | \geq { \textstyle { \frac { 2 } { 3 } } } | V |$ and that $| V _ { S e p } ^ { \prime } | \geq { \textstyle { \frac { 2 } { 3 } } } | V |$ **. We will show that in this case, the root r must have small S-distance to and at least** $\frac { 1 } { 3 } | V |$ **vertices. We**

<div class="docvortex-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3: $\operatorname { S P L I T } ( G , S , d )$
Input: A graph $\overline { { G } } = ( V , E ) .$ , a set $\overline { { S \subseteq V } }$ and a positive integer $d .$
Output: Returns a tuple $( S _ { S p l i t } , P )$ , where $S _ { S p l i t } \subseteq S$ is a separator such that no two
vertices in the same SCC in $G \setminus E ( S )$ have S-distance greater than d. $P$ is
the collection of these SCCs.
1 $S _ { S p l i t } \leftarrow \emptyset ; P \leftarrow \emptyset ; G ^ { \prime } \leftarrow G ;$
2 while $G ^ { \prime } \neq \emptyset$ do
3 Pick an arbitrary vertex r in V .
4 Run in parallel OutSeparator $\iota ( r , G ^ { \prime } , S , d / 1 6 )$ and InSeparator $. ( r , G ^ { \prime } , S , d / 1 6 )$
and let $( S _ { S e p } , V _ { S e p } )$ be the tuple returned by the first subprocedure that finishes.
5 if $\begin{array} { r } { | V _ { S e p } | \leq \frac { 2 } { 3 } | \dot { V } | } \end{array}$ then $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } ) \leftarrow ( S _ { S e p } , V _ { S e p } )$
6 else
7 Run the separator procedure that was aborted in line 4 until it finishes and let
the tuple returned by this procedure be $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } )$
8 if $\begin{array} { r } { | V _ { S e p } ^ { \prime } | \leq \frac { 2 } { 3 } | V | } \end{array}$ then
9 $( \widehat { S } _ { S m a l l } ^ { \prime } , \widehat { P } _ { S m a l l } ) \leftarrow \operatorname { S P L I T } ( G ^ { \prime } [ V _ { S e p } ^ { \prime } ] , V _ { S e p } ^ { \prime } \cap S , d )$
10 $S _ { S p l i t } \leftarrow S _ { S p l i t } \cup S _ { S m a l l } \cup S _ { S e p } ^ { \prime }$
11 $P \leftarrow P \cup P _ { S m a l l } \cup \{ \{ s \} | s \in \dot { S _ { S e p } ^ { \prime } } \} )$
12 $G ^ { \prime } \leftarrow G ^ { \prime } [ V \setminus ( V _ { S e p } ^ { \prime } \cup S _ { S e p } ^ { \prime } ) ]$
13 else
/* Init a generalized ES-tree from r to depth $d / 2$ * /
14 $\mathcal { E } _ { r } ^ { i } \gets \mathrm { I N I T \hat { G E S } } ( r , G ^ { \prime } , S , d / 2 )$
/* Find a good separator for every vertex that is far from r. $^ { * / }$
15 while $( v \gets \mathcal { E } _ { r } ^ { i } .$ GetUnreachableVertex $( ) \neq \bot$ do
16 if $\mathcal { E } _ { r } ^ { i } . \mathrm { D I S T A N C E } ( r , v ) &gt; d / 2$ then
17 $\widetilde{(S_{Step}^{\prime \prime},V_{Step}^{\prime \prime})} \xleftarrow{\widetilde{ INSEPAATOR }} \widetilde{(v,G^{\prime},S,d/4)}$
18 else // If $\mathcal { E } _ { r } ^ { i } .$ Distance $( v , r ) &gt; d / 2$
19 $\bigsqcup _ { v } \; ( S _ { S e p } ^ { \prime \prime } , V _ { S e p } ^ { \prime \prime } ) \leftarrow \mathrm { O U T S E P A R A T O R } \big ( v , G ^ { \prime } , S , d / 4 \big )$
20 $\mathcal { E } _ { r } . \operatorname { D E L E T E } ( S _ { S e p } ^ { \prime \prime } \cup V _ { S e p } ^ { \prime \prime } )$
21 $( S _ { S e p } ^ { \prime \prime \prime } , P ^ { \prime \prime \prime } ) \leftarrow \dot { \mathrm { S P L I T } } ( \dot { G [ } V _ { S e p } ^ { \prime \prime } ] , V _ { S e p } ^ { \prime \prime } \cap S , d )$
22 $S _ { S p l i t } \leftarrow S _ { S p l i t } \cup S _ { S e p } ^ { \prime \prime } \cup S _ { S e p } ^ { \prime \prime \prime }$
23 $P \leftarrow P \cup P ^ { \prime \prime \prime } \cup \{ \{ s \} | s \in \vec { S _ { S e p } ^ { \prime \prime } } \} )$
24 P ← P ∪ {Er.GetAllVertices()}
25 G′ ← ∅
26 return $( S _ { S p l i t } , P )$
</div>

**then show that this allows us to efficiently prune away at most** $\frac { 2 } { 3 } | V |$ **vertices from V at large S-distance to or from r. We recursively invoke** $\mathrm { S P L I T } ( \cdot )$ **on the induced subgraphs of vertex sets that we pruned away.**

**We analyze the procedure in detail in multiple steps, and summarize the result in lemma 6.5 that is the main result of this section. Let us first prove that if the algorithm enters the else-case in line 13 then we add an SCC of size at least** $\frac { 1 } { 3 } | V |$ to $P .$

**Claim 6.2.** If the algorithm enters line 13 then the vertex set returned by $\mathcal { E } _ { r }$ **.GetAllVertices()** in line 24 is of size at least $\frac { 1 } { 3 } | V |$

Proof. Observe first that since we did no enter the if-case in line 9, that $| V _ { S e p } |   >   { \textstyle { \frac { 2 } { 3 } } } | V |$ **and** $| V _ { S e p } ^ { \prime } | > { \textstyle \frac { 2 } { 3 } } | V |$ **(since we also cannot have entered the if case in line 5).**

**Since we could not find a sufficiently good separator in either direction, we certified that the S-out-ball from r defined**

$$
B _ { o u t } ( r ) = \{ v \in V | \mathbf { d i s t } _ { G } ( r , v , S ) \leq d / 1 6 \}
$$

has size greater than $\frac { 2 } { 3 } | V |$ **, and that similarly, the S-in-ball** $B _ { i n } ( r )$ **of r has size greater than** $\frac { 2 } { 3 } | V |$ **. This implies that**

$$
| B _ { { o u t } } ( r ) \cap B _ { { i n } } ( r ) | > \frac { 1 } { 3 } | V | .
$$

Further, we have that every vertex on a shortest-path between r and a vertex $v \in B _ { o u t } ( r ) \cap$ $B _ { i n } ( r )$ **has a shortest-path from and to r of length at most** $d / 1 6$ **. Thus the S-distance between any pair of vertices in** $B _ { o u t } ( r ) \cap B _ { i n } ( r )$ **is at most** $d / 8 .$ **. Now, let SP be the set of all vertices that are on a shortest-path w.r.t. S-distance between two vertices in** $B _ { o u t } ( r ) \cap B _ { i n } ( r )$ **. Clearly,** $B _ { o u t } ( r ) \cap B _ { i n } ( r ) \subseteq S P$ **, so** $| S P | \geq | V | / 3$ **. It is also easy to see that** $G [ S P ]$ **has S-diameter at** most $d / 4$

**At this point, the algorithm repeatedly finds a vertex v that is far from r and finds a separator from v. We will now show that the part of the cut containing v is always disjoint** from $S P ;$ since $| S P | > | V | / 3$ , this implies that at least $| V | / 3$ vertices remain in $\mathcal { E } _ { r }$

Consider some vertex v chosen in line 15. Let us say that we now run InSeparator $. ( v , G ^ { \prime } , S , d / 4 )$ the case where we run OutSeparator $( v , G ^ { \prime } , S , d / 4 )$ **is analogous. Now, by property 2 in lemma 6.1, every** $s \in S _ { S e p }$ **has dist** $( s , v , S ) \leq d / 4$ **. Thus, since we only run the InSeparator** if we have dist $( r , v , S ) > d / 2$ , we must have dist $( r , s , S ) > d / 4$ □

**We point out that claim 6.2 implies that Split(·) only recurses on disjoint subgraphs containing at most a** $2 / 3$ **fraction of the vertices of the given graph. To see this, observe that** we either recurse in line 9 on $G ^ { \prime } [ V _ { S e p } ^ { \prime } ]$ after we explicitly checked whether $| V _ { S e p } ^ { \prime } |   \leq   { \textstyle { \frac { 2 } { 3 } } } | V |$ **in the if-condition, or we recurse in line 21 on the subgraph pruned from the set of vertices that** $\mathcal { E } _ { r }$ **was initialized on. But since by claim 6.2 the remaining vertex set in** $\mathcal { E } _ { r }$ **is of size at least** $| V | / 3 ,$ , the subgraphs pruned away can contain at most $\frac { 2 } { 3 } | V |$ **vertices.**

**We can use this observation to establish correctness of the Split(·) procedure.**

**Claim 6.3. Split** $( G , S , d )$ returns a tuple $( S _ { S e p } , P )$ where $P$ is a partition of the vertex set V such that

1. for $X \in P ,$ and vertices $u , v \in X$ we have dis $\mathbf { t } _ { G \setminus E ( S _ { S e p } ) } ( u , v , S ) \leq d ,$ and

2. for distinct $X , Y \in P ,$ with vertices $u \in X$ and $v \in Y$ , u $\not \vdash _ { G \setminus E ( S _ { S e p } ) } v ,$ and

$$
\textstyle \beta . ~ \left| S _ { { S p l i t } } \right| \leq \frac { 3 2 \operatorname { l o g } n } { d } \sum _ { X \in P } \operatorname { l g } ( n - | X \cap S | ) | X \cap S | .
$$

Proof. Let us start with the first two properties which we prove by induction on the size of $| V |$ where the base case $| V | = 1$ **is easily checked. For the inductive step, observe that each SCC X in the final collection P was added to P in line 11, 23 or 24. We distinguish by 3 cases:**

**1. a vertex s was added as singleton set after appearing in a separator** $S _ { S e p }$ **but then {s} is strongly-connected and s cannot reach any other vertex in** $G \setminus E ( S _ { S e p } )$ **since it has no out-going edges, or**

2. an SCC X was added as part of a collection $P ^ { \prime \prime \prime }$ **in line 23. But then we have that the** collection $P ^ { \prime \prime \prime }$ satisfies the properties in $G [ V _ { S e p } ^ { \prime \prime } ]$ **by the induction hypothesis and since** $V _ { S e p } ^ { \prime \prime }$ was a cut side and $S _ { S e p } ^ { \prime \prime }$ **added to** $S _ { o u t }$ **, we have that there cannot be a path to** and **from any vertex in** $G \setminus E ( \dot { S _ { o u t } } )$ **, or**

**3. we added the non-trivial SCC X to P after constructing an GES-tree from some vertex** $r \in X$ **and after pruning each vertex at S-distance to/from r larger than** $d / 2$ **(see the while loop on line 15). But then each vertex that remains in** $X$ **can reach r within S-distance** $d / 2$ **and is reached from r within distance** $d / 2$ **implying that any two vertices** $u , v \in X$ **have a path from u to v of S-distance at most d.**

**Finally, let us upper bound the number of vertices in** $S _ { S p l i t }$ **. We use a classic charging argument and argue that each time we add a separator** $S _ { S e p }$ **to** $S _ { S p l i t }$ **with sides** $V _ { S e p }$ **and** $V \setminus ( V _ { S e p } \cup S _ { S e p } )$ **at least one of these sides contains at most half the S-vertices in** $V \cap S .$ **. Let X be the smaller side of the cut (in term of S-vertices) then by property 3 from lemma 6.1, we can charge each S vertex in X for** $\frac { 3 2 \log n } { d }$ separator vertices (since we invoke OutSeparator(·) and InSeparator(·) with parameter at least $d / 1 6 )$

**Observe that once we determined that a separator** $S _ { S e p }$ **t**hat is about to be added to $S _ { S p l i t }$ in line 10 or 22, we only recurse on the induced subgraph $G ^ { \prime } [ V _ { S e p } ]$ **and let the graph in the** next iteration be $G ^ { \prime } [ V \setminus ( V _ { \mathit { S e p } } \cup S _ { \mathit { S e p } } )$

**Let X be an SCC in the final collection P. Then each vertex** $v \in X$ **can only have been charged at most** $\lg ( n - | X \cap S | )$ **times. The lemma follows.** □

**It remains to bound the running time. Before we bound the overall running time, let us prove the following claim on the running time of invoking the separator procedures in parallel.**

**Claim 6.4.** We spend $O ( E ( V _ { S e p } ^ { \prime } \cup S _ { S e p } ^ { \prime } ) )$ time to find a separator in line 5 or 6.

Proof. Observe that we run the subprocedures OutSeparator $. ( r , G ^ { \prime } , S , d / 1 6 )$ and InSeparator $( r , G ^ { \prime } , S , d / 1 6 )$ **in line 4 in parallel. Therefore, when we run them, we interleave their machine operations,** computing one operation from OutSeparat $\scriptstyle \mathrm { O R } \left( r , G ^ { \prime } , S , d / 1 6 \right)$ **and then one operation from** InSeparator $\mathfrak { i } ( r , G ^ { \prime } , S , d / 1 6 )$ in turns. Let us assume that OutSeparator $. ( r , G ^ { \prime } , S , d / 1 6 )$ **is**

the first subprocedure that finishes and returns tuple $( S _ { S e p } , V _ { S e p } )$ . Then, by lemma 6.1, the sub procedure used $O ( E ( V _ { S e p } \cup S _ { S e p } ) )$ time. Since the subprocedure InSeparator $. ( r , G ^ { \prime } , S , d / 1 6 )$ ran at most one more operation than OutSeparator $. ( r , G ^ { \prime } , S , d / 1 6 )$ , it also used $O ( E ( V _ { S e p } \cup$ $\left. S _ { S e p } \right) )$ operations. A symmetric argument establishes the same bounds, if InSeparator(r, $G ^ { \prime } , S , d / 1 6 )$ **finishes first. The overhead induced by running two procedures in parallel can be made constant.**

**Since assignments take constant time, the claim is vacuously true by our discussion if the ifcase in line 9 is true. Otherwise, we compute a new separator tuple by continuing the execution of the formerly aborted separator subprocedure. But by the same argument as above, this subprocedure’s running time now clearly dominates the running time of the subprocedure that** finished first in line 4. The time to compute $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } )$ **is thus again upper bounded by** $O ( E ( V _ { S e p } ^ { \prime } ) )$ **by lemma 6.1, as required.** □

**Finally, we have established enough claims to prove lemma 6.5.**

**Lemma 6.5 (Strengthening of lemma 5.1). Split** $( G , S , d )$ returns a tuple $( S _ { S p l i t } , P )$ where P is a partition of the vertex set V such that

1. for $X \in P$ , and vertices $u , v \in X$ we have dis $\mathbf { t } _ { G \setminus E ( S _ { S p l i t } ) } ( u , v , S ) \leq d ,$ and

2. for distinct $X , Y \in P$ , with vertices $u \in X$ and $v \in Y$ , u $\not \vdash _ { G \setminus E ( S _ { S p l i t } ) } t$ v, and

3. **|S**<strong><sub>Split</sub></strong>**| ≤** 32 log nd P<sub>X</sub>∈P **lg(n − |X ∩ S|)|X ∩ S|**

The algorithm runs in time $O \left( d \textstyle \sum _ { X \in P } ( 1 + \operatorname { l g } ( n - | X | ) ) E ( X ) \right)$

Proof. **Since correctness was established in lemma 6.3, it only remains to bound the running time of the procedure. Let us first bound the running time without recursive calls to procedure** Split $( G , S , d )$ . To see that we only spend $O ( | E ( G ) | d )$ time in $\operatorname { S P L I T } ( G , S , d )$ excluding recursive calls, observe first that we can find each separator tuple $( S _ { S e p } ^ { \prime } , V _ { S e p } ^ { \prime } )$ in time $O ( E ( V _ { S e p } ^ { \prime } ) )$ **by** claim 6.4. We then, either recurse on $G ^ { \prime } [ V _ { S e p } ^ { \prime } ] )$ and remove the vertices $V _ { S e p } ^ { \prime } \cup S _ { S e p } ^ { \prime }$ **with their incident edges from** $G ^ { \prime }$ **or we enter the else-case (line 13). Clearly, if our algorithm never visits the else-case, we only spend time** $O ( | E ( G ) | )$ **excluding the recursive calls since we immediately remove the edge set that we found in the separator from the graph.**

We further observe that the running time for the GES-tree can be bounded by $O ( | E ( G ) | d )$ **The time to compute the separators to prune vertices away from the GES-tree is again combined at most** $O ( | E ( G ) | )$ **by lemma 6.1 and the observation that we remove edges from the graph G after they were scanned by one such separator procedure.**

**We already discussed that claim 6.2 implies that we only recurse on disjoint subgraphs with at most** $\frac { 2 } { 3 } | V |$ **vertices. We obtain that each vertex in a final SCC X in P participated in at most** $O ( \stackrel { \circ } { \log } ( n - | X | ) )$ **levels of recursion and so did its incident edges hence we can then** bound the total running time by $O \left( d \textstyle \sum _ { X \in P } ( 1 + \operatorname { l o g } ( n - | X | ) ) E ( X ) \right)$ □

## 7 Handling deletions

**Let us now consider how to process the deletion of an edge** $( u , v )$ **which we describe in pseudo code in algorithm 4. We fix our data structure in a bottom-up procedure where we first remove** the edge $( u , v )$ if it is contained in any induced subgraph $\hat { G } _ { i } [ X ]$ from the GES $\mathcal { E } _ { \mathrm { C E N T E R } ( X ) }$

Then, we check if any GES $\mathcal { E } _ { \mathrm { C E N T E R } ( X ) }$ on a subgraph $\hat { G } _ { i } [ X ]$ **contains a node that became unreachable due to the edge deletion or the fixing procedure on a level below. Whilst there** is such a GES $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ , we first find a separator $S _ { S e p }$ from $X ^ { \prime }$ **in lines 7 or 9. We now consider two cases based on the size of the set Flatten** $\left( V _ { S e p } \right)$ **. Whilst focusing on the size of** $\operatorname { F L A T T E N } ( V _ { S e p } )$ **instead of the size of** $V _ { S e p }$ **seems like a minor detail, it is essential to consider the underlying vertex set instead of the node set, since the node set can be further split by node split updates from lower levels.**

**Now, let us consider the first case, when the set** $V _ { S e p }$ **separated by** $S _ { S e p }$ **is small (with regard to Flatten** $( V _ { S e p } ) )$ **; in this case, we simply prune** $V _ { S e p }$ **from our tree by adding** $S _ { S e p }$ **to** $S _ { i + 1 }$ , and then invoke $\operatorname { \dot { S P L I T } } ( \hat { G } _ { i } [ V _ { S e p } ] , V _ { S e p } \cap S _ { i } , \delta / 2 )$ to get a collection of subgraphs $P ^ { \prime }$ **where** each subgraph $Y \in P ^ { \prime }$ **has every pair of nodes** $A , B \in Y$ **at** $S _ { i }$ **-distance** $\delta / 2$ **. (We can afford to invoke Split on the vertex set** $V _ { S e p }$ **because we can afford to recurse to on the smaller side of a cut.)**

**The second case is when** $V _ { S e p }$ **is large compared to the number of vertices in node set of the GES-tree. In this case we do not add** $S _ { S e p }$ **to** $S _ { i + 1 }$ **. Instead we we declare the GES-**tree $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ **invalid, and delete the entire tree. We then partition the set X that we are working with by invoking the Split procedure on all of X. (Intuitively, this step is expensive, but we will show that whenever it occurs, there is a constant probability that the graph has decomposed into smaller SCCs, and we have thus made progress.)**

**Finally, we use the new partition and construct on each induced subgraph a new GES-tree** at a randomly chosen center. This is done by the procedure InitNewPartition $( P ^ { \prime } , i , \delta )$ **t**hat was presented in subsection 5. We then apply the updates to the graph $\hat { G } _ { i + 1 }$ **using the GES-tree operations defined in lemma 4.3. Note, that we include the separator vertices as singleton sets in the partition and therefore invoke** $\mathcal { E } _ { X } . \operatorname { S P L I T N O D E } ( \cdot )$ **on each singleton before invoking** $\mathcal { E } _ { X }$ .Augment $( S _ { S e p } ^ { \prime \prime } )$ **which ensures that the assumption from lemma 4.3 is satisfied. As in the last section, let us prove the following two lemmas whose proofs will further justify some of the details of the algorithm.**

**We start by showing that because we root the GES-tree for SCC X at a** random **root r, if the GES-tree ends up being deleted in 16 in algorithm 4, this means that with constant probability X has decomposed into smaller SCCs, and so progress has been made.**

**Lemma 7.1 (c.f. also [Che+16], Lemma 13).** Consider an GES $\mathcal { E } _ { r }   =   \mathcal { E } _ { \mathrm { C E N T E R } } ( X )$ that was initialized on the induced graph of some node set $X _ { I n i t }$ , with $X \subseteq X _ { I n i t }$ , and that is deleted in line 16 in algorithm $4 \cdot$ Then with probability at least ${ \frac { 2 } { 3 } } ,$ the partition $P ^ { \prime \prime }$ computed in line 17 satisfies that each $X ^ { \prime } \in P ^ { \prime \prime }$ has $| { \operatorname { F L A T T E N } } ( X ^ { \prime } ) | \leq \textstyle \frac { 2 } { 3 } | { \operatorname { F L A T T E N } } ( X _ { { I n i t } } ) |$

Proof. **Let i be the level of our hierarchy on which** $\mathcal { E } _ { r }$ **was initialized, i.e.** $\mathcal { E } _ { r }$ **was initialized on** graph $\hat { G } _ { i } [ X _ { I n i t } ]$ **, and went up to depth δ with respect to** $S _ { i }$ **-distances (see Algorithm 2).**

<div class="docvortex-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 4: Delete(u, v)
Input: An edge $( u , v ) \in E$
Result: Updates the data structure such that queries for the graph $G \setminus \{ ( u , v ) \}$ can be
answered in constant time.
1 for $i = 0$ to $\left[ \log n \right]$ do
2 if If there exists an $X \in \hat { V } _ { i + 1 }$ with $u , v \in X$ then
3 $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ .Delete $( u , v )$
4 while there exists an $X \in \hat { V } _ { i + 1 }$ with $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ .GetUnreachable() $\neq \perp$ do
5 $X ^ { \prime } \leftarrow \mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ .GetUnreachable()
/* Find a separator from $X ^ { \prime }$ depending on whether $X ^ { \prime }$ is far to
reach from r or the other way around. */
6 if $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) } . \operatorname { D I S T A N C E } ( \operatorname { C E N T E R } ( X ) , X ^ { \prime } ) &gt; \delta$ then
7 $\bigsqcup _ { n } ( S _ { S e p } , \widetilde { V _ { S e p } } ) \leftarrow \operatorname { I N S E P A R A T O R } ( X ^ { \prime } , \hat { G } _ { i } [ X ] , X \cap S _ { i } , \delta / 2 )$
8 else // $\mathcal { E } _ { \mathtt { C E N T E R } ( X ) }$ .Distance(X′, Center $( X ) ) &gt; \delta$
9 $\bigsqcup _ { e } ( S _ { S e p } , V _ { S e p } ) \overset { \curvearrowright } { \leftarrow } \operatorname { O U T S E P A R A T O R } ( X ^ { \prime } , \hat { G } _ { i } [ X ] , X \cap S _ { i } , \delta / 2 )$
/* If the separator is chosen such that $V _ { S e p }$ is small, we have a
good separator, therefore we remove $V _ { S e p }$ from $\mathcal { E } _ { r }$ and maintain
the SCCs in $\hat { G } _ { i } [ V _ { S e p } ]$ separately. Otherwise, we delete the entire
GES $\mathcal { E } _ { \mathtt { C E N T E R } ( X ) }$ and partition the graph with a good separator. */
10 if |Flatten(VSep)| ≤ 2|Flatten(X)| then
11 $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) } . \operatorname { D E L E T E } ( V _ { S e p } \cup S _ { S e p } )$
12 $\begin{array} { r } { ( S _ { S e p } ^ { \prime } , P ^ { \prime } ) \leftarrow \mathrm { S P L I T } ( \hat { G } [ V _ { S e p } ] , V _ { S e p } \cap S _ { i } , \delta / 2 ) } \end{array}$
13 $S _ { S e p } ^ { \prime \prime } \gets S _ { S e p } \cup S _ { S e p } ^ { \prime }$
14 $P ^ { \prime \prime } \leftarrow P ^ { \prime } \cup S _ { S e p }$
15 else
16 $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ .Delete()
17 $\widehat { ( S _ { S e p } ^ { \prime \prime } , P ^ { \prime \prime } ) } \leftarrow \operatorname { S P L I T } ( \hat { G } _ { i } [ X ] , X \cap S _ { i } , \delta / 2 )$
/* After finding the new partitions, we init them, execute the
vertex splits on the next level and add the separator vertices.
*/
18 InitNewPartition $( P ^ { \prime \prime } , i , \delta )$
19 foreach $Y \in P ^ { \prime \prime }$ do
20 $\mathcal { E } _ { \operatorname { C E N T E R } ( X ) }$ .SplitNode(Y )
21 ECenter(X).Augment $( S _ { S e p } ^ { \prime \prime } )$
22 $S _ { i + 1 } \leftarrow S _ { i + 1 } \cup S _ { S e p } ^ { \prime \prime }$
</div>

**Let** $u _ { 1 } , u _ { 2 } ,$ **.. be the sequence of updates since the GES-tree** $\mathcal { E } _ { r }$ **was initialized that were** either adversarial edge deletions, nodes added to $S _ { i }$ or node splits in the graph $\hat { G } _ { i } [ X _ { I n i t } ]$ Observe that this sequence is independent of how we choose our random root $r ,$ **since they occur at a lower level, and so do not take any GES-trees at level i into account. Recall, also, that the adversary cannot learn anything about** $r$ **from our answers to queries because the SCCs of the graph are objective, and so do not reveal any information about our algorithm.** We refer to the remaining updates on $\hat { G } _ { i } [ X _ { I n i t } ]$ **as** separator **updates, which are the updates adding nodes to** $S _ { i + 1 }$ **and removing edges incident to** $S _ { i + 1 }$ **or between nodes that due to such edge deletions are no longer strongly-connected. We point out that the separator updates are heavily dependent on how we chose our random source. The update sequence that the GES-tree undergoes up to its deletion in line 16 is a mixture of the former updates that are independent of our chosen root** $r$ **and the separator updates.**

Let $G ^ { j }$ **be the** graph $\hat { G } _ { i }$ after the update sequence $u _ { 1 } , u _ { 2 } , . . . , u _ { j }$ is applied. Let $X _ { m a x } ^ { j }$ be the component of S<sub>i</sub>-diameter at most $\delta / 2$ that maximizes the cardinality of $\operatorname { F L A T T E N } ( X _ { m a x } ^ { j } )$ **in** $G ^ { j }$ . We choose $X _ { m a x } ^ { j }$ **in this way because we want to establish an upper bound on the largest** SCC of $S _ { i }$ -diameter at most $\delta / 2$ in $G ^ { j }$ **. We then show that that if a randomly chosen source** deletes a GES-tree (see line 16) after $j$ updates, then there is a good probability that $X _ { m a x } ^ { j }$ is small. Then by the guarantees of lemma 5.1, the $\mathrm { S P L I T } ( \cdot )$ **procedure in line 17 partitions** the vertices into SCCs $X ^ { \prime }$ of $S _ { i }$ -diameter at most $\delta / 2$ , which all have small $\left| \operatorname { F L A T T E N } ( X ^ { \prime } ) \right|$ because $X _ { m a x } ^ { j }$ **is small.**

More precisely, let $G _ { r } ^ { j } ,$ be the graph is obtained by applying all updates up to update $u _ { j }$ **to** $\hat { G } _ { i } [ X _ { I n i t } ] ;$ **he**re we include the updates $u _ { 1 } , . . . , u _ { j }$ , as well as all separator updates up to the time when $u _ { j }$ takes place. (Observe that $G ^ { j }$ **is** independent from the choice of $r ,$ but $G _ { r } ^ { j }$ is not.) Let $X _ { m a x , r } ^ { j }$ **be the component of** $S _ { i }$ **-diameter at most** $\delta / 2$ **that maximizes the cardinality** of $\mathrm { F L A T T E N } ( X _ { m a x , r } ^ { j } )$ in this graph $G _ { r } ^ { j }$ **. It is straight-forward to see that since** $S _ { i }$ **-distances** can only increase due to separator updates, we have $| \operatorname { F L A T T E N } ( X _ { m a x , r } ^ { j } ) | \leq | \operatorname { F L A T T E N } ( X _ { m a x } ^ { j } ) |$ for any $r .$ Further $| \mathrm { F L A T T E N } ( X _ { m a x , r } ^ { j } ) |$ upper bounds the size of any component $X ^ { \prime }   \in   P ^ { \prime \prime }$ $\mathrm { i . e . } \quad | \mathrm { F L A T T E N } ( X ^ { \prime } ) |   \leq   | \mathrm { F L A T T E N } ( X _ { m a x , r } ^ { j } ) |$ **if the tree** $\mathcal { E } _ { r }$ **is deleted in line 16 while handling update** $u _ { j } ;$ **the same bound holds if** $\mathcal { E } _ { r }$ **is deleted after update** $u _ { j }$ **, because the cardinality of** Flatten $( X _ { m a x , r } ^ { j } )$ monotonically decreases in $j ,$ i.e. |Flatten $| ( X _ { m a x , r } ^ { \mathring { j } } ) | \leq | \mathrm { F L A T T E N } \big ( X _ { m a x , r } ^ { j - 1 } \big ) |$ since updates can only increase $S _ { i }$ **-distances.**

**Now, let k be the index, such that**

$$
\begin{aligned} { \big | \operatorname { F L A T T E N } ( X _ { m a x } ^ { k } ) \big | \leq \frac { 2 } { 3 } \big | \operatorname { F L A T T E N } ( X _ { I n i t } ) \big | < \big | \operatorname { F L A T T E N } ( X _ { m a x } ^ { k - 1 } ) \big | . } \\ \end{aligned}
$$

i.e. k is chosen such that after the update sequence $u _ { 1 } , u _ { 2 } , . . . , u _ { k }$ were applied to $\hat { G } _ { i } [ X _ { I n i t } ]$ **, there** exists no SCC X in $G ^ { k }$ of diameter at most $\delta / 2$ with $\textstyle | \operatorname { F L A T T E N } ( X ) | > \frac { 2 } { 3 } | \operatorname { F L A T T E N } ( X _ { I n i t } ) |$

**In the remainder of the proof, we establish the following claim: if we chose some vertex** $r   \in   \mathrm { F L A T T E N } \big ( X _ { m a x } ^ { k - 1 } \big )$ **, then the GES-tree would not be been deleted before update** $u _ { k }$ **took place. Before we prove this claim, let us point out that this implies the lemma: observe that by the independence of how we choose r and the update sequence** $u _ { 1 } , u _ { 2 } , . . ,$ **we have that**

$$
P r [ r \in X _ { m a x } ^ { k - 1 } | u _ { 1 } , u _ { 2 } , . . ] = P r [ r \in X _ { m a x } ^ { k - 1 } ] = \frac { \left| \operatorname { F L A T T E N } \left( X _ { m a x } ^ { k - 1 } \right) \right| } { \left| \operatorname { F L A T T E N } \left( X _ { I n i t } \right) \right. } > \frac { 2 } { 3 }
$$

**where the before-last equality follows from the fact that we choose the root uniformly at random** among the vertices in $\operatorname { F L A T T E N } ( X _ { I n i t } )$ Thus, with probability at least ${ \frac { 2 } { 3 } } ,$ **we chose a root whose GES-tree is deleted during or after the update** $u _ { k }$ **and therefore the invoked procedure** Split(·) ensures that every SCC $X ^ { \prime }   \in   P ^ { \prime \prime }$ satisfies $\left| \operatorname { F L A T T E N } ( X ^ { \prime } ) \right|   \leq   \left| \operatorname { F L A T T E N } ( X _ { m a x } ^ { k } ) \right|   \leq$ $\textstyle \frac { 2 } { 3 } \big | \overset { \frown } { \operatorname { F L A T T E N } } ( X _ { { I n i t } } ) \big |$ **, as required.**

Now, let us prove the final claim. We want to show that if $r   \in   X _ { m a x } ^ { k - 1 }$ **, then the GES-tree would not have been deleted before update** $u _ { k }$ **. To do so, we need to show that even if we include the separator updates, the SCC containing** $r$ **continues to have size at least** $\textstyle \frac { 2 } { 3 } | \operatorname { F L A T T E N } ( X _ { { I n i t } } ) |$ **before update** $u _ { k }$ **. In particular, we argue that before update** $u _ { k }$ **, none of** the separator updates decrease the size of $X _ { m a x } ^ { k - 1 }$ **. The reason is that the InSeparator computed in Line 7 of Algorithm 4 is always run from a node** $X$ **whose** $S _ { i ^ { * } }$ **-distance from** $r$ **is at least δ. (The argument for an OutSeparator in Line 9 is analogous.) Now, the InSeparator from X is computed up to S**<strong><sub>i</sub></strong>**-distance** $\delta / 2$ **, so by Property 2 of Lemma 6.1, we have that all nodes pruned away from the component have S**<strong><sub>i</sub></strong>**-distance at most** $\delta / 2$ **to** $X ;$ **this implies that these** nodes have $S _ { i } .$ -distance more than $\delta / 2$ from $r ,$ and so cannot be in $X _ { m a x } ^ { k - 1 }$ , because $X _ { m a x } ^ { k - 1 }$ **was** defined to have $S _ { i } .$ -diameter at most $\delta / 2 .$ Thus none of the separator updates affect $X _ { m a x } ^ { k - 1 }$ before update $u _ { k }$ **, which concludes the proof of the lemma.**

Next, let us analyze the size of the sets $S _ { i }$ . We analyze $S _ { i }$ **using the inequality below in** order to ease the proof of the lemma. We point out that the term $\lg ( n - | X \cup S _ { i } | )$ **approaches lg n as the SCC X splits further into smaller pieces. Our lemma can therefore be stated more easily, see therefore corollary 7.3.**

**Lemma 7.2.** During the entire course of deletions our algorithm maintains

$$
\begin{aligned} { | S _ { 0 } | } & { { } = n } \\ { | S _ { i + 1 } | } & { { } \leq \frac { 3 2 \operatorname { l o g } n } { \delta } \sum _ { X \in \hat { V } _ { i } } \operatorname { l g } ( n - | X \cap S _ { i } | ) | X \cap S _ { i } | \quad \mathit { f o r } \; i \geq 0 } \\ \end{aligned}\tag{1}
$$

**(2)**

Proof. **We prove by induction on i. It is easy to see that** $S _ { 0 }$ **has cardinality n since we initialize it to the node set in procedure 1, and since each set** $S _ { i }$ **i**s an increasing set over time.

**Let us therefore focus on** $i > 0$ **. Let us first assume that the separator nodes were added by the procedure OutSeparator(·) (analogously InSeparator(·)). Since the procedure is** invoked on an induced subgraph $\hat { G } _ { i } [ X ]$ **t**hat was formerly strongly-connected, we have that **either** $V _ { S e p }$ **or** $X \setminus ( V _ { S e p } \cup S _ { S e p } )$ **(or both) contain at most half the** $S _ { i }$ **-nodes originally in X. Let Y be such a side. Since adding** $S _ { S e p }$ **to** $S _ { i }$ **separates the two sides, we have that RHS of the equation is increased by at least** $\textstyle { \frac { 3 2 \log n } { \delta } } | Y \cap S _ { i } |$ since $\lg ( n - | Y \cap S _ { i } | ) | Y \cap S _ { i } | - \lg ( n - | X \cap$ $S _ { i } | ) | Y \cap S _ { i } | \geq | Y \cap S _ { i } |$ . **Si**nce we increase the LHS by at most $\textstyle { \frac { 4 \log n } { \delta } } | Y \cap S _ { i } |$ **by the guarantees in lemma 6.1, the inequality is still holds.**

**Otherwise, separator nodes were added due to procedure** $\mathrm { S P L I T } ( \cdot )$ **But then we can straight-forwardly apply lemma 6.5 which immediately implies that the inequality still holds.**

**Finally, the hierarchy might augment the set** $S _ { i }$ **i**n line 21, but we observe that $f ( s ) =$ $\lg ( n   -   s )   *   s$ is a function increasing in s for $s \leq { \textstyle { \frac { 1 } { 2 } } } n$ **which can be proven by finding the** **derivative. Thus adding nodes to the set** $S _ { i }$ **can only increase the RHS whilst the LHS remains unchanged.** □

**Corollary 7.3.** During the entire course of deletions, we have $\textstyle | S _ { i + 1 } |   \leq   { \frac { 1 6 \operatorname { l g } ^ { 2 } n } { \delta } } | S _ { i } |$ , for any $i \geq 0$

## 8 Putting it all together

By corollary 7.3, using $\delta = 6 4 \lg ^ { 2 } n ,$ we enforce that each $| S _ { i } | \leq n / 2 ^ { i }$ , so $\hat { G } _ { \lfloor \lg n \rfloor + 1 }$ **i**s indeed the **condensation of G. Thus, we can return on queries asking whether u and v are in the same** SCC of G, simply by checking whether they are represented by the same node in $\hat { G } _ { \lfloor \lg n \rfloor + 1 }$ **which can be done in constant time.**

**We now upper bound the running time of our algorithm by** $O ( m \log ^ { 5 } n )$ **and then refine** the analysis slightly to obtain the claimed running time of $O ( m \log ^ { 4 } n )$

**By lemma 7.1, we have that with probability** $\frac { 2 } { 3 }$ **, that every time a node leaves a GES, its induced subgraph contains at most a fraction of** $\frac{2}{3}$ of the underlying vertices of the initial graph. Thus, in expectation each vertex in $V$ participates on each level in $O ( \log n )$ GES-trees. Each time it contributes to the GES-trees running time by its degree times the depth of the GES-tree which we fixed to be $\delta .$ Thus we have expected time $\textstyle O ( \sum _ { v \in V } \mathbf { d e g } ( v ) \delta \operatorname { l o g } n ) = O ( m \operatorname { l o g } ^ { 3 } n )$ to maintain all the GES-trees on a single level by lemma 4.3. There are $O ( \log n )$ **levels in the** hierarchy, so the total expected running time is bounded by $O ( m \log ^ { 4 } n )$

**By lemmas 6.5, the running time for invoking** $\operatorname { S P L I T } ( G [ X ] , S , \delta / 2 )$ **can be bounded by** $O ( E ( X ) \delta \log n )   =   O ( E ( X ) \log ^ { 3 } n )$ **. After we invoke** $\operatorname { S P L I T } ( G [ X ] , S , \delta / 2 )$ **in algorithm 4, we expect with constant probability again by lemma 7.1, that each vertex is at most O(log n) times in an SCC on which the** $\mathrm { S P L I T } ( \cdot )$ **procedure is invoked upon. We therefore conclude that** total expected running time per level is $O ( m \log ^ { 4 } n )$ , and the overall total is $O ( m \log ^ { 5 } n )$

**Finally, we can bound the total running time incurred by all invocations of InSeparator(·) and OutSeparator(·) outside of Split(·) by the same argument and obtain total running** time $O ( m \log ^ { 2 } n )$ since each invocation takes time $O ( E ( G ) )$ on a graph $G .$

**This completes the running time analysis, establishing the total expected running time** $O ( m \log ^ { 5 } n )$ **.** We point out that the bottleneck of our algorithm are the invocations of $\mathrm { S P L I T } ( \cdot )$ We can reduce the total expected cost of these invocations to $O ( m \log ^ { 4 } n )$ **by using the more involved upper bound on the running time of Split(·) of**

$$
O \left( \delta E ( X ) + \delta \sum _ { X \in P } \operatorname { l o g } ( n - | \operatorname { F L A T T E N } ( X ) | ) E ( X ) \right)
$$

**where we use** $\left| \operatorname { F L A T T E N } ( X ) \right|$ **instead of** $\left| X \right|$ **to capture node splits. Then, we can bound the costs incurred by the first part of the bound by** $O ( m \log ^ { 4 } n )$ **; for the second part we also get a bound** $O ( m \log ^ { 4 } n )$ **by using a telescoping sum argument on the size of the graph.**

**This concludes our proof of theorem 1.1.**

## 9 Conclusion

**In this article, we presented the first algorithm that maintains SCCs or SSR in decremental graphs in almost-linear expected total update time** $\tilde { O } ( m )$ **. Previously, the fastest algorithm** for maintaining the SCCs or SSR achieved expected total update time $\tilde { O } ( m \sqrt { n } )$ **. Three main open questions arise in the context of our new algorithm:**

**• Can the complexity of the Single-Source Shortest-Path problem in decremental directed graphs be improved beyond total expected update time of** $O ( m n ^ { 0 . 9 + o ( 1 ) } )$ **[HKN14b; HKN15] and can it even match the time complexity achieved by our algorithm?**

**• Does there exist a** deterministic **algorithm to maintain SCCs/SSR in a decremental graph beyond the** $O ( m n )$ **total update time complexity?**

**• And finally, is there a algorithm that solves All-Pairs Reachability in fully-dynamic graphs with update time** $\tilde { O } ( m )$ **and constant query time? Such an algorithm is already** known for dense graphs[DI04] but is still unknown for graphs of sparsity $O ( n ^ { 2 - \epsilon } )$

**Acknowledgements The second author of the paper would like to thank Jacob Evald for some helpful comments on organization and correctness.**

## References

[AW14] Amir Abboud and Virginia Vassilevska Williams. “Popular conjectures imply strong lower bounds for dynamic problems”. In: Foundations of Computer Science (FOCS), 2014 IEEE 55th Annual Symposium on. IEEE. 2014, pp. 434–443 (cit. on p. 2).

[BC16] Aaron Bernstein and Shiri Chechik. “Deterministic decremental single source shortest paths: beyond the o (mn) bound”. In: Proceedings of the forty-eighth annual ACM symposium on Theory of Computing. ACM. 2016, pp. 389–397 (cit. on p. 3).

[BC17] Aaron Bernstein and Shiri Chechik. “Deterministic partially dynamic single source shortest paths for sparse graphs”. In: Proceedings of the Twenty-Eighth Annual ACM-SIAM Symposium on Discrete Algorithms. SIAM. 2017, pp. 453–469 (cit. on p. 3).

[Che+16] Shiri Chechik, Thomas Dueholm Hansen, Giuseppe F Italiano, Jakub Łącki, and Nikos Parotsidis. “Decremental single-source reachability and strongly connected components in O (m√ n) total update time”. In: Foundations of Computer Science (FOCS), 2016 IEEE 57th Annual Symposium on. IEEE. 2016, pp. 315–324 (cit. on pp. 2, 6, 7, 20).

[Cor+09] Thomas H Cormen, Charles E Leiserson, Ronald L Rivest, and Clifford Stein. Introduction to algorithms. MIT press, 2009 (cit. on p. 2).

[DI04] Camil Demetrescu and Giuseppe F Italiano. “A new approach to dynamic all pairs shortest paths”. In: Journal of the ACM (JACM) 51.6 (2004), pp. 968–992 (cit. on p. 25).

[ES81] Shimon Even and Yossi Shiloach. “An on-line edge-deletion problem”. In: Journal of the ACM (JACM) 28.1 (1981), pp. 1–4 (cit. on pp. 2, 3, 6, 8, 10).

[HDT01] Jacob Holm, Kristian De Lichtenberg, and Mikkel Thorup. “Poly-logarithmic deterministic fully-dynamic algorithms for connectivity, minimum spanning tree, 2- edge, and biconnectivity”. In: Journal of the ACM (JACM) 48.4 (2001), pp. 723–760 (cit. on p. 2).

[HK95] Monika Rauch Henzinger and Valerie King. “Fully dynamic biconnectivity and transitive closure”. In: Foundations of Computer Science, 1995. Proceedings., 36th Annual Symposium on. IEEE. 1995, pp. 664–672 (cit. on pp. 3, 6, 10).

[HKN14a] Monika Henzinger, Sebastian Krinninger, and Danupon Nanongkai. “Decremental single-source shortest paths on undirected graphs in near-linear total update time”. In: Foundations of Computer Science (FOCS), 2014 IEEE 55th Annual Symposium on. IEEE. 2014, pp. 146–155 (cit. on p. 3).

[HKN14b] Monika Henzinger, Sebastian Krinninger, and Danupon Nanongkai. “Sublineartime decremental algorithms for single-source reachability and shortest paths on directed graphs”. In: Proceedings of the forty-sixth annual ACM symposium on Theory of computing. ACM. 2014, pp. 674–683 (cit. on pp. 2, 3, 25).

[HKN15] Monika Henzinger, Sebastian Krinninger, and Danupon Nanongkai. “Improved algorithms for decremental single-source reachability on directed graphs”. In: International Colloquium on Automata, Languages, and Programming. Springer. 2015, pp. 725–736 (cit. on pp. 2, 3, 25).

[Hua+17] Shang-En Huang, Dawei Huang, Tsvi Kopelowitz, and Seth Pettie. “Fully dynamic connectivity in O (log n (log log n) 2) amortized expected time”. In: Proceedings of the twenty-eighth Annual ACM-SIAM Symposium on Discrete Algorithms. Society for Industrial and Applied Mathematics. 2017, pp. 510–520 (cit. on p. 2).

[Ita+17] Giuseppe F Italiano, Adam Karczmarz, Jakub Łącki, and Piotr Sankowski. “Decremental single-source reachability in planar digraphs”. In: Proceedings of the 49th Annual ACM SIGACT Symposium on Theory of Computing. ACM. 2017, pp. 1108–1121 (cit. on p. 2).

[Ita88] Giuseppe F Italiano. “Finding paths and deleting edges in directed acyclic graphs”. In: Information Processing Letters 28.1 (1988), pp. 5–11 (cit. on pp. 8, 10).

[Łąc13] Jakub Łącki. “Improved deterministic algorithms for decremental reachability and strongly connected components”. In: ACM Transactions on Algorithms (TALG) 9.3 (2013), p. 27 (cit. on pp. 2, 3, 7).

[NSW17] Danupon Nanongkai, Thatchaphol Saranurak, and Christian Wulff-Nilsen. “Dynamic minimum spanning forest with subpolynomial worst-case update time”. In: Foundations of Computer Science (FOCS), 2017 IEEE 58th Annual Symposium on. IEEE. 2017, pp. 950–961 (cit. on p. 2).

[RZ08] Liam Roditty and Uri Zwick. “Improved dynamic reachability algorithms for directed graphs”. In: SIAM Journal on Computing 37.5 (2008), pp. 1455–1471 (cit. on pp. 2, 7).

[RZ16] Liam Roditty and Uri Zwick. “A fully dynamic reachability algorithm for directed graphs with an almost linear update time”. In: SIAM Journal on Computing 45.3 (2016), pp. 712–733 (cit. on p. 3).

[Tar72] Robert Tarjan. “Depth-first search and linear graph algorithms”. In: SIAM journal on computing 1.2 (1972), pp. 146–160 (cit. on pp. 2, 12).

[Tho00] Mikkel Thorup. “Near-optimal fully-dynamic graph connectivity”. In: Proceedings of the thirty-second annual ACM symposium on Theory of computing. ACM. 2000, pp. 343–350 (cit. on p. 2).

[Tho07] Mikkel Thorup. “Fully-dynamic min-cut”. In: Combinatorica 27.1 (2007), pp. 91–127 (cit. on p. 2).

[Wul13] Christian Wulff-Nilsen. “Faster deterministic fully-dynamic graph connectivity”. In: Proceedings of the twenty-fourth annual ACM-SIAM symposium on Discrete algorithms. Society for Industrial and Applied Mathematics. 2013, pp. 1757–1769 (cit. on p. 2).

## A Fully-Dynamic Reachability from many sources

**Theorem A.1.** Given a directed graph $G = ( V , E ) ,   S \subseteq V$ , we can maintain a data structure that supports the operations:

$\operatorname { I N S E R T } ( u , E _ { u } )$ : Adds u to V with edges $E _ { u }$ where each edge in $E _ { u }$ has an endpoint u.

• **Delete(u)**: Deletes u from V .

• **Query(u, v)**: For $u \in S , v \in V$ , returns whether u has a path to v.

with expected amortized update time $O \left( \frac { | S | m \operatorname { l o g } ^ { 4 } n } { t } \right)$ and worst-case query time $O ( t )$ for any $t \in [ 1 , | S | ]$ . The bound holds against an oblivious adaptive adversary.

**The algorithm to implement theorem A.1 can be described as follows: Initiate the data structure by constructing a decremental SSR structure as described in theorem 1.1 from each vertex** $s \in S .$ **. Initialize a set I to be the empty set. Consider an update: if a deletion occurs, remove the edges incident to u from each SSR structure, if an insertion occurs reinitialize the SSR structures at u on the most recent graph G and add u to I.** $If $| I | \geq t ,$$ **reinitialize the entire data structure. On query for** $( u , v ) ,   u \in S$ **, check the SSR structure at u whether it reaches** $v .$ **Then check for each** $r$ **in I whether u reaches** $r$ **and** $r$ **reaches v. If any of these queries is successful, return that u reaches** $v .$ **Otherwise, return that u cannot reach v. It is straight-forward to argue for correctness, and the running time is attained since the SSR structure require** $O ( | S | m \log ^ { 4 } n )$ **total time which can be amortized over t updates. Each insertion additionally requires time** $O ( m \log ^ { 4 } n )$ **to (re)initialize the SSR structure at** ${ \mathcal { U } } .$ **The query time is clearly** $O ( t )$ **since we check reachability from and to each** $r \in I$ **in constant time. The theorem follows.**

## B Proof of Lemma 4.2

Proof. We define the edge weight $w ( u , v )$ of an edge $( u , v )$ to be $w ( u , v ) = 1 \; { \mathrm { i f } } \; ( u , v ) \in E _ { o u t } ( S )$ and $w ( u , v ) = 0$ **otherwise. On invocation of InitGES(r, G, S, δ), we find a shortest-path tree** $T$ **to depth δ from** $r$ **in** $G$ **by running a weighted BFS. Each edge in** $T$ **is called a** tree edge **and each edge in** $E \setminus T$ **is a** non-tree edge**. We assign each vertex** $v \in V ,$ **a distance label** $l ( v )$ **t**hat **is initialized to dis** $\mathbf { t } _ { G } ( r , v )$ **. We also maintain with each vertex a set LevelEdges(v) that is initialized to** $E _ { i n } ( v ) \setminus E _ { o u t } ( v )$ **that is all edges in** $E _ { i n } ( v )$ **after removing self-loops.**

**Now, consider an update of the form Delete(u, v). If** $( u , v )   \not \in   T$ **, then simply remove** $( u , v )$ **from** $G$ **and LevelEdges(v) and return since the shortest-path tree** $T$ **did not change. If** $( u , v ) \in T$ **, we remove** $( u , v )$ **from** $T$ **and add v to the min-queue** $Q$ **with value** $l ( v )$ **. We let** $Q . \mathrm { M I N ( ) }$ return the minimum value of any element in $Q$ and if Q is empty, we let $Q . \mathrm { M I N } ( ) = \infty$

**Whilst** $Q . \mathrm { M I N } ( ) < \delta + 1$ **, we obtain the vertex** $v = Q . { \mathrm { M I N E L E M E N T } } ( )$ **We then iteratively extract an edge** $( y , v )$ **from LevelEdges(v) and check if** $l ( v ) = l ( y ) + w ( y , v )$ **. We stop if we found such an edge or if LevelEdges(v) is empty. In the former case, we add** $( y , v )$ **to** $T$ **and remove v from** $Q$ **since** $T$ **contains a new path of length** $l ( v )$ **from r to v. In the latter case, we** **know that v cannot be reconnected in** $T$ **at the same distance. We therefore increase the level** $l ( v )$ **by one. We then remove all edges** $( v , z ) \in T \cap E _ { o u t } ( v )$ **from** $T$ **and add each z to the queue Q with its current level** $l ( z )$ **as value. We also update the level of v in** $Q$ **and if** $l ( v ) \leq \delta$ **, we add all edges in** $E _ { i n } ( v ) \setminus E _ { o u t } ( v )$ **again to LevelEdges(v). Once** $Q . \mathrm { M I N } ( { \overline { { { {  } } } } } ) \geq \delta + 1$ **, we remove all remaining vertices from** $Q ,$ **, set their distance level to ∞ and remove their incident edges from the graph G.**

**We observe that the queue** $Q$ **can be implemented with constant operation time using two lists since we never add a vertex with level larger than the current min-elements level plus one. Clearly, we check each edge** $( y , v )$ **in LevelEdges(v) once for any level of v and the condition** $l ( v ) = l ( y ) + w ( y , v )$ **can be checked in constant time. The set LevelEdges(v) partitions the edges and since removing edges in** $E _ { o u t } ( v ) \cap T { \mathrm { ~ i f ~ } } l ( v )$ **increases can be amortized over edge checks for each disconnected vertex, we conclude that the total running time can be bound by** $\textstyle O ( \sum _ { v \in V } E _ { i n } ( v ) \delta ) = O ( m \delta )$

P**Let us now argue for correctness of the algorithm. We observe that we only delete an edge** $( y , v )$ **from T if** $l ( v )   >   l ( y ) + w ( y , v )$ **which happens if** $l ( y )$ **is increased or** $( y , v )$ **is removed. After removing** $( y , v )$ **, we take the first edge** $( u , v )$ **in LevelEdges(v) that reconnects at the same level** $l ( v )$ **, i.e. if** $l ( v ) = l ( u ) + w ( u , v )$ **. Since the levels only increase over time and edge weights are fixed, we have that once** $l ( v ) < l ( u ) + w ( u , v )$ **, we cannot use** $( u , v )$ **to reconnect v at the same level. Thus, if LevelEdges(v) is empty, we certified that v cannot be reconnected at level** $l ( v )$ **. We also observe that after the loop to fix a vertex in** $Q$ **finished, that for all edges in** $T ,   l ( v )   =   l ( y ) + w ( y , v )$ **, because we remove an edge** $( y , v )$ **from** $T$ **if** $l ( y )$ **increases. Now assume that when** $Q . \mathrm { M I N ( ) } = \infty$ **, that** $T$ **is always a tree of the vertices in** $V$ **that have level** $< \infty$ **. It follows that** $T$ **is a shortest-path tree by the discussion above. To see that** $T$ **is indeed always a tree, observe that since** $l ( v )   =   l ( y ) + w ( y , v )$ **is always enforced on edges in** $T$ **and edge weights are non-negative, that we have for any two vertices** $y , v \in V$ **on a common cycle** that $l ( y ) = l ( v )$ , implying that all edge weights are 0. But since the edge weights of $E _ { o u t } ( S )$ are set to 1, this implies that the cycle does not contain a vertex in $S ,$ **. But this contradicts the assumption that S is a feedback vertex set.**

**Clearly, the operation Distance(r, v) can be implemented by returning** $l ( v )$ **in constant time. To obtain Distance(v, r), we also construct our data structure on the reversed edge set of G from r. To support Delete(V**′), we simply delete all incident edges from vertices in $V ^ { \prime }$ using $\operatorname { D E L E T E } ( u , v )$ and remove all vertices $V ^ { \prime }$ from $V .$ **The operation GetUnreachableVertex()** can be implemented by keeping a list of all vertices with level $\infty$ □

## C Proof of lemma 4.3

Proof. **Let us first describe how to implement the operations efficiently. We maintain additional pointers from each vertex** $v   \in   V$ **to the set** $X   \in   \hat { V }$ **with** $v   \in   X$ **and store with each vertex in** $\hat { V }$ **the number of vertices it represents. For SplitVertex(X), we use any vertex in** $x \in X$ **to locate the vertex** $Y \in { \hat { V } }$ **with** $X \subseteq Y$ **. If** $X = Y$ **, we return. Otherwise, we compare** the sizes of X and $Y \setminus X$ and if X has larger cardinality, we invoke SplitVertex $( Y \setminus X )$ and return. Let us therefore assume that X is smaller th**an** $Y \setminus X$ **. Then, we create a new** **vertex X in** $\hat { G }$ **and move all edges in** $E ( X )$ **from** $E ( Y )$ **. In particular, we also let the set** Level $\operatorname { E D G E } ( X )   =   \operatorname { L E V E L E D G E S } ( Y ) \cap E _ { i n } ( X )$ . We might also move the tree edge in $T$ de**pending on whether its endpoint maps to X or** $Y \setminus X$ **. Finally, we set** $l ( X )$ **to** $l ( Y )$ **, remove the vertices in X from** $Y$ **, add the vertices in** $\hat { V }$ **t**hat have no in-coming tree edge and do not **contain r to the queue** $Q$ **and invoke the fixing process described in the preceding lemma.**

**Clearly, the operation of moving the edges from Y to X takes time** $O ( E ( X ) )$ **. Since each time an edge is moved, at least one of its endpoints underlying vertex set halves, we have that each edge is moved at most** $O ( \log X )$ **times, where** $X$ **is the initial endpoint of larger cardinality. The second part of the upper bound of the lemma follows.**

**It is also straight-forward to see that after shifting the edges, the level of the vertices X and** $Y \setminus X$ **is at least** $l ( Y )$ **and that each edge in** $E _ { i n } ( Y ) \setminus \operatorname { L E V E L E D G E S } ( Y )$ **was already certified to not reconnect X or** $Y \setminus X$ **to level** $l ( Y )$ **. Thus, the fixing process is simply part of the standard fixing process and can be included in the analysis presented for the last lemma.**

Finally, we implement the operation Augment $( S ^ { \prime } )$ **by increasing the weight of each edge** $E _ { o u t } ( S ^ { \prime } \setminus S )$ to 1. We then remove each tree edge $( s ^ { \prime } , v ) \in T \cap E _ { o u t } ( S ^ { \prime } \setminus S )$ **from** $T ;$ **add each such v to Q and invoke the fixing procedure. It is straight-forward to show that the costs of this procedure are subsumed by the fixing procedure.** □

## D Proof of Lemma 6.1

Proof. Let an out-layer $L _ { o u t } ( r , G , S , i )$ be defined to the vertices that are at distance ex**actly i from r, i.e.** $L _ { o u t } ( r , G , S , i ) \; = \; \{ v \; \in \; V | \mathbf { d i s t } _ { G } ( r , v , S ) \; = \; i \}$ **Thus,** $L _ { o u t } ( r , G , S , i )$ **∩** $L _ { o u t } ( r , G , S , j ) = \emptyset$ for $i \neq j$ . We can compute $L _ { o u t } ( r , G , S , 0 )$ in time $O ( E _ { o u t } ( L _ { o u t } ( r , G , S , 0 ) ) )$ time, by initializing a queue $Q _ { 0 }$ **with element r and then iteratively extracting a vertex v from** $Q _ { 0 }$ **and adding for each** $( v , w ) \in E _ { o u t } ( v )$ **the vertex w to** $Q _ { 0 }$ **if** $w \not \in S$ **and if w was not visited by the algorithm before. Initializing the queue** $Q _ { i + 1 }$ **with the vertex set** $L _ { o u t } ( r , G , S , i ) \cap S$ **, we can use the same strategy for computing** $L _ { o u t } ( r , G , S , i \mathrm { ~ + ~ } 1 )$ **in time** $O ( E _ { o u t } ( L _ { o u t } ( r , G , S , i ) ) + E _ { o u t } ( L _ { o u t } ( r , G , S , i + 1 ) ) )$ **. This corresponds to running a BFS on an edge set with weights in** $\{ 0 , 1 \}$ **. Upon finding the first i such that**

$$
| L _ { i } \cap S | \leq \frac { \operatorname* { m i n } \{ \sum _ { j < i } | L _ { j } \cap S | , | ( V \setminus \sum _ { j < i } L _ { j } ) \cap S | \} 2 \operatorname { l o g } n } { d }
$$

**is satisfied, and then output** $S _ { S e p } = L _ { i } \cap S$ **and** $V _ { S e p } = \cup _ { j \leq i } L _ { i } \setminus S _ { S e p } .$ **Since we never extract the vertices in** $S _ { S e p }$ **from the queue but only look at the out-going edges from** $V _ { S e p }$ **we conclude** that the procedure takes time $O ( E _ { o u t } ( V _ { S e p } ) )$

To see, that there exists at least one layer i satisfying this inequality, let layer $i ^ { \prime }$ **be the** minimal layer such that $\textstyle \sum _ { j < i ^ { \prime } } | L _ { j } \cap S | > { \frac { 1 } { 2 } } | S |$ . If $i ^ { \prime } \geq d / 2$ **, then we claim there exists at least** one layer $i \leq i ^ { \prime }$ **with**

$$
| L _ { i } \cap S | \leq \frac { \sum _ { j < i } | L _ { j } \cap S | 2 \operatorname { l o g } n } { d }
$$

Otherwise, i.e. if $i ^ { \prime } \geq d / 2$ , there we claim that there exists at least one layer $i \leq i ^ { \prime }$ **with**

$$
| L _ { i } \cap S | \leq \frac { \sum _ { j < i } | L _ { j } \cap S | 2 \operatorname { l o g } n } { d }
$$

**Let us assume the former case. Consider for the sake of contradiction that we cannot find** an appropriate $i \leq d / 2$ , i.e. $\textstyle | L _ { i } \cap S | > \frac { \sum _ { j < i } | L _ { j } \cap S | \operatorname { l o g } n } { d }$ for any i. Then, we have $\textstyle \sum _ { j < i } | L _ { j } \cap$ $\begin{array} { r } { | S |   >   ( 1 + \frac { 2 \log n } { d } ) ^ { i } } \end{array}$ since the set grows by factor $\textstyle ( 1 + { \frac { 2 \log n } { d } } )$ with each iteration and it would be trivially satisfied if $L _ { 0 } \cap S   =   \emptyset$ . But then the final set must be of size greater than $\textstyle n   =   e ^ { \log n }   \leq   \bigl ( 1   +   \frac { 2 \log n } { d } \bigr ) ^ { d / 2 }$ , thus establishing a contradiction. The case where $i ^ { \prime }   \geq   d / 2$ **i**s **symmetric.**

**For point 4. in our lemma, we observe that removing a layer implies that the layers visited can not reach the layers not visited yet. Assume for contradiction that this is not true, then we have an edge** $( x , y )$ **with** $x \in V _ { S e p }$ **and** $y \in V \setminus ( S _ { S e p } \cup V _ { S e p } )$ **but then y has to be in the same or the next layer that x is contained. In the first case,** $y \in V _ { S e p }$ **which contradicts that** $y \in V \setminus ( S _ { S e p } \cup V _ { S e p } )$ **. In the latter case, Either** $y \in V _ { S e p }$ **or y is in the removed layer** $S _ { S e p }$ **but** both contradicts again that $y \in V \setminus ( S _ { S e p } \cup V _ { S e p } )$ □