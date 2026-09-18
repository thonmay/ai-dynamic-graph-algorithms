# yang2019dynamic

*Source: yang2019dynamic.pdf*
*Pages: 13*

## Page 1

### Fully Dynamic Depth-First Search in Directed Graphs
Bohua Yang♮, Dong Wen♮, Lu Qin♮, Ying Zhang♮, Xubo Wang♮, and Xuemin Lin§
♮Centre for Artiﬁcial Intelligence, University of Technology Sydney, Australia
§The University of New South Wales, Australia
♮bohua.yang@student.uts.edu.au; {dong.wen, lu.qin, ying.zhang, xubo.wang}@uts.edu.au;
§lxue@cse.unsw.edu.au;
#### ABSTRACT
Depth-ﬁrst search (DFS) is a fundamental and important al-
gorithm in graph analysis. It is the basis of many graph algo-
rithms such as computing strongly connected components,
testing planarity, and detecting biconnected components.
The result of a DFS is normally shown as a DFS-Tree. Given
the frequent updates in many real-world graphs (e.g., social
networks and communication networks), we study the prob-
lem of DFS-Tree maintenance in dynamic directed graphs.
In the literature, most works focus on the DFS-Tree main-
tenance problem in undirected graphs and directed acyclic
graphs.
However, their methods cannot easily be applied
in the case of general directed graphs. Motivated by this,
we propose a framework and corresponding algorithms for
both edge insertion and deletion in general directed graphs.
We further give several optimizations to speed up the algo-
rithms. We conduct extensive experiments on 12 real-world
datasets to show the eﬃciency of our proposed algorithms.
PVLDB Reference Format:
Bohua Yang, Dong Wen, Lu Qin, Ying Zhang, Xubo Wang and
Xuemin Lin. Fully Dynamic Depth-First Search in Directed Graphs.
PVLDB, 13(2): 142-154, 2019.
DOI: https://doi.org/10.14778/3364324.3364329
#### 1.
#### INTRODUCTION
Depth-ﬁrst search (DFS)1 is an algorithm to traverse a
graph. It searches the vertices along a graph as far as pos-
sible in each branch before backtracking. The process of a
DFS is naturally represented as a search spanning tree fol-
lowing the depth-ﬁrst order, named the DFS-Tree. Given
a graph G in Figure 1(a), one possible DFS-Tree T of G
is shown in Figure 1(b). The time complexity for perform-
ing a DFS traversal and generating a DFS-Tree in a graph
G(V, E) is O(|V | + |E|) [20].
DFS is a fundamental algorithm in graph analysis and
is the basis for eﬃciently solving numerous graph problems,
such as testing graph reachability [19,24], detecting strongly
1https://en.wikipedia.org/wiki/Depth-first_search
This
work
is
licensed
under
the
Creative
Commons
Attribution-
NonCommercial-NoDerivatives 4.0 International License. To view a copy
of this license, visit http://creativecommons.org/licenses/by-nc-nd/4.0/. For
any use beyond those covered by this license, obtain permission by emailing
info@vldb.org. Copyright is held by the owner/author(s). Publication rights
licensed to the VLDB Endowment.
Proceedings of the VLDB Endowment, Vol. 13, No. 2
ISSN 2150-8097.
DOI: https://doi.org/10.14778/3364324.3364329
v10
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
(a) The graph G
v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
(b) A DFS-Tree T of G
Figure 1: An example graph G and its DFS-Tree T .
γ is a virtual root connecting all vertices in G.
connected components [9,17,20], detecting biconnected com-
ponents [11], ﬁnding graph bridges [21], ﬁnding paths, de-
tecting cycles [23], testing bipartiteness, testing graph pla-
narity [8,12], and topological sorting [22]. These algorithms
perform DFS traversal as a subroutine. They require access
to vertices in the depth-ﬁrst order.
In many real-world applications, graphs dynamically up-
date over time. Given the importance of DFS, the DFS-Tree
maintenance problem in dynamic directed graphs is insuf-
ﬁciently studied. In this paper, we examine this problem,
which is to update the DFS-Tree for an inserted or deleted
edge. The aforementioned applications of DFS beneﬁt from
this study.
Speciﬁcally, in many graph problems such as
computing strongly connected components [20], biconnected
components [11], and ﬁnding graph bridges [21], a key step
is to compute the reachable ancestor with the lowest depth
of each vertex in the DFS-Tree. Based on this study, we
can simply ﬁnish this task by directly tracking the updated
DFS-Tree of the graph.
For example, in detecting bicon-
nected components, it is required to compute a DFS-Tree of
the graph and then traverse the tree to get the shallowest po-
sition that each vertex can reach. When the graph updates,
we can derive an updated DFS-Tree instead of performing
the DFS traversal from scratch. We can also simultaneously
maintain the interval label (discovery time and ﬁnish time)
of each vertex as a byproduct in the DFS-Tree. The interval
label is used in several works [19,24] as a part of the index
to test the graph reachability. These works ﬁlter out the
queries if two vertices are connected in the tree, and it only
takes constant time to check the reachability in the tree us-
ing the interval labels. Based on the study in this paper,
we can immediately derive the updated interval labels when
the graph updates instead of rerunning DFS. In addition, in
142

## Page 2

puzzle problems such as mazes, users can check the updated
interval labels to eﬃciently identify the connectivity from
the entrance to the goal when the maze updates. They can
also directly search the updated DFS-Tree to ﬁnd a solution.
Existing Works and Challenges. The DFS-Tree main-
tenance problem for directed acyclic graphs and undirected
graphs has been well studied in the literature.
However,
these techniques cannot be applied to the DFS-Tree main-
tenance of general directed graphs.
For directed acyclic graphs, [10] and [2] investigate the
DFS-Tree maintenance problem under incremental settings
and decremental settings, respectively. Franciosa et al. [10]
update the DFS-Tree by locating a range of vertices accord-
ing to the postorder of the DFS-Tree. They only reconstruct
the tree structure for the located range of vertices. Correct-
ness is guaranteed by the property of directed acyclic graphs
that there is no backward edge in its DFS-Tree. However,
if we follow the same procedure as that in [10] in general
directed graphs, a backward edge starting from a vertex in
the located range and ending at a vertex outside the range
may become a forward-cross edge after the update is ﬁn-
ished.
Here, an edge (s, t) is a forward-cross edge if s is
visited before t in the preorder of the tree, and there is no
ancestor-descendant relationship between s and t. A tree
with any forward-cross edge is not a valid DFS-Tree. Con-
sidering a deleted tree edge (u, v), the decremental algorithm
proposed by Baswana and Choudhary [2] iteratively ﬁnds a
new position for each vertex in the subtree of v following the
topological order. The property of directed acyclic graphs
guarantees that the in-neighbors of a vertex do not contain
its descendants in the DFS-Tree, whereas in general directed
graphs, a vertex may have a descendant as a potential parent
which cannot be appended back to the tree.
Baswana et al. [1, 4] and Chen et al. [5, 6] propose fully
dynamic algorithms to maintain the DFS-Tree in undirected
graphs. They partition the DFS-Tree into disjoint subtrees
and paths. The property of undirected graphs guarantees
that there is no cross edge between subtrees, and the neigh-
bor of a vertex appears either as its ancestor or its descen-
dant in the DFS-Tree. However, these properties are not
applicable to directed graphs since a directed graph may
have cross edges in its DFS-Tree, and two adjacent vertices
do not always have ancestor-descendant relationships.
Baswana et al. [3] design an incremental algorithm to
maintain a DFS-Tree in general directed graphs based on the
algorithm presented in [10]. They make use of a structure
called stick, which is a long downward path from the root on
which there is no branching after a large number of edge in-
sertions [3]. However, the stick structure may be broken due
to the edge deletion. Therefore, their algorithm cannot be
easily used in the fully dynamic setting. Motivated by the
above limitations, we propose eﬃcient, easy-to-implement,
and fully dynamic algorithms for DFS-Tree maintenance in
general directed graphs.
Our Solution. Given a graph G and its DFS-Tree T , it
is necessary to update the DFS-Tree T if a forward-cross
edge has been inserted or a tree edge has been deleted. We
use the time intervals to eﬃciently check the edge type in
constant time, where the time interval of a vertex u is an in-
terval starting from the discovery timestamp and ending at
the ﬁnish timestamp of u in DFS. For the clarity of presen-
tation, we add a virtual root γ connecting all vertices in the
graph, so there always exists a DFS-Tree for any graph. An
edge removal operation for edge (s, t) can be transformed
into appending the subtree rooted at t to end of the chil-
dren list of the virtual root γ, and this step may generate
several new forward-cross edges due to the back movement
of the subtree. Therefore, the tree update is essentially to
eliminate the forward-cross edges for both edge insertion
and deletion. Instead of naively reconstructing the whole
DFS-Tree, we ﬁrst propose a general framework for the tree
update based on the concept of time interval. The key step
in the framework is to set a range called candidate inter-
val. The candidate interval locates a small set of vertices.
We replace the DFS-subtree induced by these vertices by
performing DFS only for these vertices in the new graph,
whereas the other part of the DFS-Tree remains unchanged.
We give the implementations for both edge insertion and
deletion.
By carefully setting the candidate interval, the
computed DFS-Tree is guaranteed to be valid.
To improve the algorithmic eﬃciency of the basic imple-
mentation, we propose several optimizations for both edge
insertion and deletion from two perspectives. First, we aim
to reﬁne the candidate interval and reduce the number of
inﬂuenced vertices. Instead of using a ﬁxed candidate in-
terval, we adopt a new strategy that dynamically updates
the candidate interval during the process of DFS. We guar-
antee that the search scope is at most the same as that in
the basic algorithm in the worst case. Second, we transform
a part of the graph search to the tree search. Recall that
in the basic implementation, we scan the out-neighbors of
all located vertices in DFS to collect their children in the
updated DFS-Tree. We observe that the (tree) children of
a set of vertices in the old DFS-Tree can be reused in the
updated DFS-Tree, so we avoid scanning the out-neighbors
of these vertices in the graph. Our experiments show that
the proportion of this kind of vertices is very large, and this
optimization greatly speeds up the algorithm especially in
large graphs with many high-degree vertices.
Contributions. We summarize the main contributions in
this paper as follows.
• A general and ﬂexible framework. We design a novel
framework for both edge insertion and deletion.
To
the best of our knowledge, we are the ﬁrst to study
the fully dynamic DFS-Tree maintenance problem in
general directed graphs from the perspective of prac-
tical implementation.
• Easy-to-implement algorithms. We develop algorithms
based on the proposed framework for both operations.
The algorithms are easy to implement in practice.
• Two groups of optimizations. We optimize the algo-
rithms for both operations in two directions. One is
to tighten the candidate interval.
This reduces the
search scope and guarantees that the running time of
algorithms only depends on the neighbors of vertices
whose visiting time has been changed in the updated
DFS-Tree. The other one is to scan the children in the
DFS-Tree instead of the out-neighbors in the graph for
a large proportion of visited vertices. This optimiza-
tion further improves the algorithmic eﬃciency.
• Extensive experiments. We conduct experiments on 12
real-world networks to show the performance of our
proposed algorithms and the eﬀectiveness of our opti-
mizations.
143

## Page 3

Table 1: Notations
Notation
Description
Nin(u)
the in-neighbors of vertex u
Nout(u)
the out-neighbors of vertex u
C(u)
the children list of vertex u in the DFS-Tree T
T (u)
the vertex set in the subtree rooted at u in T
IT (u)
the time interval of u in T
T [t]
the visited vertex at the timestamp t in T
T [l, r]
the visited vertex set in the interval [l, r] in T
T (I)
equivalent to T [I.left, I.right]
Tnew
the updated DFS-Tree
Outline.
The rest of this paper is organized as follows.
Section 2 introduces background knowledge about DFS and
deﬁnes the research problem. Section 3 introduces related
works. Section 4 gives a framework for DFS-Tree mainte-
nance. Section 5 gives the basic implementation for both
edge insertion and deletion. Section 6 studies the optimiza-
tions. Section 7 reports the experiment result, and Section 8
concludes the paper. Due to the space limitation, we omit
the detailed proof for some lemmas and theorems if they are
extremely straightforward.
#### 2.
#### PRELIMINARY
We study a directed graph G(V, E), where V is the set
of vertices and E is the set of edges in G.
The number
of vertices and edges are denoted by n and m respectively,
i.e., n = |V | and m = |E|. Given a vertex u, we denote
the in-neighbors (resp. out-neighbors) of u by Nin(u) (resp.
Nout(u)), and denote the in-degree (resp. out-degree) of u
by din(u) = |Nin(u)| (resp. dout(u) = |Nout(u)|). Several
frequently used notations are summarized in Table 1.
Definition 1. (Depth-First Search) Given a graph G,
a depth-ﬁrst search (DFS) traverses G in a particular order
by picking an unvisited vertex v from the out-neighbors of the
most recently visited vertex u to search, and backtracks to the
vertex from where it came when a vertex u has explored all
possible ways to search further. [7]
For simplicity and without loss of generality, we add a
virtual root vertex γ and connect γ to every vertex in G.
We always perform the DFS traversal starting from γ and
collect all vertices.
Definition 2. (DFS-Tree) Given a graph G, a DFS-Tree
of G, denoted by TG, is an ordered spanning tree formed by
the process of DFS. [7]
Algorithm 1: DFS(u)
Input: a graph G, and a root vertex u in G
Output: a DFS-Tree T
1 mark u as visited;
2 foreach v ∈Nout(u): v is unvisited do
3
append v to the end of children list C(u) in T ;
4
DFS(v);
We omit the subscript G of TG when the context is clear.
Given a vertex u, we denote C(u) the children list of u in the
DFS-Tree T . Note that the DFS-Tree is not unique. There
is a one-to-one correspondence between a vertex search order
and a DFS-Tree. We give the pseudocode for computing the
DFS-Tree in Algorithm 1, which is self-explanatory. Given
an example graph G in Figure 1(a), one possible DFS-Tree
T of graph G is shown in Figure 1(b).
v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
(a) Types of non-tree edges
v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
�1, 40]
�2, 7]
�3, 6]
�4, 5]
�8, 37]
�9, 10]
�11, 24]
�12, 21]
�13, 14]
�15, 18]
�16, 17]
�19, 20]
�22, 23]
�25, 32]
�26, 29]
�27, 28]
�30, 31]
�34, 35]
�33, 36]
�38, 39]
(b) Time intervals
Figure 2: The non-tree edges and time intervals of
the DFS-Tree T .
The Validity of the DFS-Tree. Given a graph G and
any search spanning tree T of G, the edges appearing in
the tree are called tree edges. The remaining edges (u, v)
are called non-tree edges and are categorized into one the
following four types:
• (u, v) is a forward edge if u is an ancestor of v in T .
• (u, v) is a backward edge if u is a descendant of v in T .
• (u, v) is a forward-cross edge if u and v do not have
an ancestor/descendant relationship, and u is visited
before v in the preorder of T .
• (u, v) is a backward-cross edge if u and v do not have
an ancestor/descendant relationship, and u is visited
after v in the preorder of T .
Example 1. We show the non-tree edges for the DFS-Tree
T of Figure 1(b) in Figure 2(a).
The edge (v3, v10) is a
forward edge since v3 is the ancestor of v10. (v2, v0) is a
backward edge since v2 is a descendant of v0. (v7, v2) is a
backward-cross edge since v7 is visited after v2, and these
two vertices do not have an ancestor/descendant relation-
ship. There is no forward-cross edge in T .
Lemma 1. Given a graph G, a search spanning tree of G is
a DFS-Tree if and only if there is no forward-cross edge in
G under this tree. [18]
Problem Deﬁnition. In this paper, we study the problem
of maintaining the DFS-Tree in dynamic directed graphs.
Formally, given a directed graph G and a DFS-Tree T of
G, we aim to eﬃciently compute a search spanning tree of
G without any forward-cross edge when an edge is inserted
into or deleted from G.
Note that we only focus on the edge operation since the
vertex update can be implemented by several edge updates.
#### 3.
#### RELATED WORK
Reif [15] shows that the ordered DFS problem is a P-
complete problem. Here, the ordered DFS problem traverses
the graph according to the order speciﬁed by the adjacency
lists, and the ordered DFS-Tree is unique. Reif [16] and Mil-
tersen et al. [13] prove that the P-completeness of a problem
implies hardness of the problem in a dynamic environment.
In addition to the hardness of the ordered DFS-Tree mainte-
nance problem, in the literature, the DFS-Tree maintenance
problem in directed acyclic graphs [2, 10] and undirected
graphs [1,4–6] has been well studied. However, as discussed
in Section 1, these techniques cannot be applied to the fully
dynamic DFS-Tree maintenance of general directed graphs.
144

## Page 4

For directed acyclic graphs, Franciosa et al. [10] propose
an incremental algorithm to maintain a DFS-Tree under a
sequence of edge insertions in O(mn) total time. Baswana
and Choudhary [2] propose a randomized decremental al-
gorithm to maintain a DFS-Tree under a sequence of edge
deletions with expected O(mn log n) total time. Baswana et
al. [3] extend the incremental algorithm for directed acyclic
graphs presented in [10] to general directed graphs.
For undirected graphs, Baswana et al. [1] propose a fully
dynamic algorithm for maintaining a DFS-Tree under a se-
quence of updates with O(√mn log2.5 n) time per update,
an incremental algorithm for maintaining a DFS-Tree un-
der a sequence of edge insertions with O(n log3 n) time per
edge insertion, and a fault-tolerant algorithm for comput-
ing a DFS-Tree of graph G \ F with O(nk log4 n) time un-
der any set F of k failed vertices or edges [1].
The time
complexities of the above algorithms are further improved
by Chen et al. [5, 6] to O(√mn log1.5 n) for the fully dy-
namic algorithm, O(n) for the incremental algorithm, and
O(nk log2 n) for the fault-tolerant algorithm. Nakamura and
Sadakane [14] optimize the space occupied by the data struc-
ture in the above algorithms from O(m log2 n) to O(m log n).
Moreover, Baswana et al. [4] improve the above algorithms
to achieve O(√mn log n) time for the fully dynamic algo-
rithm and O(n(k′ + log n) log n) time for the fault-tolerant
algorithm, where k′ is the maximum number of failed ver-
tices/edges along any root-leaf path of the initial DFS-Tree.
#### 4.
#### A FLEXIBLE FRAMEWORK
In this section, we ﬁrst introduce several important con-
cepts in checking the validity of the DFS-Tree, then present
a framework for the DFS maintenance problem.
#### 4.1
#### Efﬁcient Validity Check
As mentioned in the previous sections, a valid DFS-Tree
does not contain any forward-cross edge. Note that for a
deleted tree edge (s, t), we can ﬁrst connect the tree by ap-
pending t to the end of the children list of the visual root
γ. Several new forward-cross edges may appear as a result.
Therefore, handling the edge deletion can also be trans-
formed to the problem of eliminating froward-cross edges.
Given an edge (s, t), we can eﬃciently check the edge type
using the time interval of each vertex instead of scanning
the out-neighbors (resp. in-neighbors) of s (resp. t) in the
graph.
Definition 3. (Time Interval) Given a DFS-Tree T and
a vertex u, the time interval of u is denoted as IT (u) =
[x, y], where x = IT (u).left is the discovery timestamp of
u in the DFS traversal, and y = IT (u).right is the ﬁnish
timestamp of u when its out-neighbors have been examined
completely in the DFS traversal. [7]
Corollary 1. There exists a one-to-one correspondence be-
tween the DFS-Tree and the time interval of each vertex.
We omit the subscript T of IT when the context is clear.
We give the time interval of every vertex in the DFS-Tree
T of Figure 1(b) in Figure 2(b). In the rest of this paper,
we always use the term discovery u and ﬁnish u to represent
the timestamp I(u).left and I(u).right respectively. The
term visit u means either discovery u or ﬁnish u.
Given a timestamp t (1 ≤t ≤2n) and the DFS-Tree T , we
denote T [t] the visited vertex at timestamp t, i.e., T [t] = v
iﬀI(v).left = t ∨I(v).right = t. For example, T [12] = v6
in Figure 2(b). Given a time interval I, we denote T (I) (or
T [I.left, I.right]) the visited vertex set no earlier than the
timestamp I.left and no later than the timestamp I.right,
i.e., T (I) = {v ∈V |I.left ≤I(v).left ≤I.right ∨I.left ≤
I(v).right ≤I.right}. For example, T [8, 15] = {v3, v4, v5, v6,
v7, v8} in Figure 2(b).
We always use the term search spanning tree to denote the
tree structure that may contain forward-cross edges in the
rest. Based on the concept of the time interval, a non-tree
edge (s, t) in a search spanning tree is
• a forward edge if I(t) ⊂I(s),
• a backward edge if I(s) ⊂I(t),
• a forward-cross edge if I(s).right < I(t).left, or
• a backward-cross edge if I(t).right < I(s).left.
To eﬃciently check the edge types, we maintain the time
interval of each vertex in addition to the tree structure.
#### 4.2
#### The Framework
To eliminate the forward-cross edges in a search spanning
tree, the general idea of our framework is to locate a can-
didate part of the tree, then reconstruct the tree structure
and recompute the time intervals of this part. We propose a
one-pass strategy. By one-pass, we mean to simultaneously
update the tree structure and the time interval of each vis-
ited vertex. In addition, we also propose optimizations that
dynamically reﬁne the range in Section 6. The pseudocode
of the framework is given in Algorithm 2.
Algorithm 2: DFS-Maintenance Framework
Input: a directed graph G, a search spanning tree T
with forward-cross edges
Output: the updated DFS-Tree
1 set a candidate time interval CI;
2 r ←LCA(T [CI.left], T [CI.right]);
3 ts ←CI.left;
4 ConstrainedDFS(r);
5 return the updated DFS-Tree T ;
Algorithm 3: ConstrainedDFS(u)
1 mark u as visited;
2 if I(u).left ≥CI.left then
3
I(u).left ←ts, ts ←ts + 1;
4 foreach v ∈Nout(u): I(v) ∩CI̸ = ∅∧I(v)̸ ⊃CI ∧v
is unvisited do
5
if I(v).left ≥CI.left then
6
v′ ←T [ts −1];
7
if v′ = u then
8
reassign v to the ﬁrst element in C(u);
9
else
10
reassign v to the next element of v′ in C(u);
11
ConstrainedDFS(v);
12 if I(u).right ≤CI.right then
13
I(u).right ←ts, ts ←ts + 1;
We locate a part of the DFS-Tree by setting a candidate
time interval CI (line 1). Let r be the lowest common an-
cestor (LCA) of the ﬁrst visited vertex T [CI.left] and the
last visited vertex T [CI.right] (line 2). We perform a con-
strained DFS starting from r (line 4). Here, by constrained,
we mean only to visit the vertices falling in the candidate
time interval CI during the DFS.
145

## Page 5

The pseudocode of ConstrainedDFS is given in Algorithm 3.
Note that the initial state of every vertex in the graph is
unvisited in all the algorithms proposed in this paper. The
variables CI and ts are global variables. We update the dis-
covery time of u if the original discovery time of u falls in
the interval CI (lines 2–3). Then, we recursively discover the
out-neighbor v of u if v falls in CI (lines 4–11). Note that in
line 4, I(v)∩CI̸ = ∅∧I(v)̸ ⊃CI is equivalent to v ∈T (CI).
In line 7, v′ = u means that v is the ﬁrst discovered child
after discovering u. Otherwise, v′ is the last ﬁnished child of
u before v. We recursively search the constrained neighbors
of v by invoking ConstrainedDFS(v) in line 11. Finally, we
update the ﬁnish time of u if its original ﬁnish time falls in
the interval CI (lines 12–13).
#### 4.3
#### Framework Analysis
Correctness Analysis. We prove the correctness of Algo-
rithm 2 in this subsection. We use T to denote the input
search spanning tree in Algorithm 2. We add the subscript
new in the tree notation (shown as Tnew) when necessary
for clarity to represent the updated search spanning tree
returned by Algorithm 2.
Lemma 2. Given any time interval CI in a search spanning
tree T , the lowest common ancestor of all vertices visited
during CI is the same as that of the ﬁrst and the last vis-
ited vertices during CI, i.e., LCA(T [CI.left], T [CI.right]) =
LCA(T (CI)).
Proof. Let u = T [CI.left], v = T [CI.right], w be the
LCA of u and v, and w′ be the LCA of T (CI). Since both
w and w′ are the ancestor of u and all the ancestors of u are
on the simple path from u to the root, either w and w′ have
an ancestor-descendant relationship or they are the same
vertex. To derive w′ = w, we show w is not the ancestor of
w′ and vice versa.
First, w is not the ancestor of w′. Otherwise, the LCA of
u and v would be w′. Second, we prove that w is not the
descendant of w′ by contradiction. Assume that w is the
descendant of w′. There is a vertex u′ in T (CI) such that u′
is not the descendant of w. Then, either u′ is the ancestor
of w, or u′ and w do not have an ancestor-descendant rela-
tionship. For the ﬁrst case, we have I(u′) ⊃CI, and for the
second case, we have I(u′) ∩CI = ∅since I(u′) ∩I(w) = ∅
and I(w) ⊇CI.
Both two cases contradict that u′ is in
T (CI).
Lemma 3. For each vertex v ∈T (CI) in Algorithm 2, either
v = r or there is a tree path from r to v such that each vertex
in the path (excluding r) is in T (CI).
Proof. We prove it by contradiction. Assume that there
is a vertex v ∈T (CI) and v̸ = r, and the parent v′ of v
satisﬁes v′̸ = r and v′̸ ∈T (CI). Then, either I(v′) ∩CI = ∅
or I(v′) ⊃CI.
For the ﬁrst case, we have I(v) ∩CI = ∅because I(v) ⊂
I(v′).
This contradicts that v ∈T (CI).
For the second
case, r is the LCA of all vertices in T (CI) based on Lemma 2.
However, if I(v′) ⊃CI, we hold that v′ is the LCA of all ver-
tices in T (CI), since v′ is the common ancestor of T [CI.left]
and T [CI.right], and v′ is a descendant of r. This contra-
dicts that r is the LCA of all vertices in T (CI).
Based on the above two lemmas, there is an invocation
for ConstrainedDFS() for each vertex v ∈T (CI), and we do
not lose any vertex belonging to T (CI) in the constrained
DFS. On the other hand, given the limitation in line 4 of
Algorithm 3, we guarantee that if a vertex v is visited in the
original tree during the interval CI, v will also be visited
in the updated tree during CI. A formal lemma is given as
follows.
Lemma 4. For each vertex v in Algorithm 2, ITnew(v).left
(resp. ITnew(v).right) falls in CI if and only if IT (v).left
(resp. IT (v).right) falls in CI, i.e., T (CI) = Tnew(CI).
Theorem 1. Given an input search spanning tree T of G,
Algorithm 2 computes a valid DFS-Tree if (i) there is no
forward-cross edge (u, v) in T such that u ∈V \ T (CI); and
(ii) there is no forward-cross edge (u, v) in Tnew such that
u ∈T (CI) ∧I(v).left > CI.right.
Proof. The updated search spanning tree Tnew com-
puted by Algorithm 2 is a DFS-Tree if and only if there is no
forward-cross edge (u, v) in Tnew. Two vertices u, v ∈V can
be considered in the following four cases: (i) u ∈T (CI)∧v ∈
T (CI), (ii) u ∈T (CI)∧v ∈V \T (CI), (iii) u ∈V \T (CI)∧
v ∈T (CI), and (iv) u ∈V \ T (CI) ∧v ∈V \ T (CI).
For the case (i), Algorithm 3 guarantees that there is no
forward-cross edge (u, v) in Tnew such that u ∈T (CI) ∧v ∈
T (CI). Because if the edge (u, v) exists, v would be visited
in the invocation of ConstrainedDFS(u).
For the case (ii), the condition (ii) in the theorem guaran-
tees that there is no forward-cross edge (u, v) in Tnew such
that u ∈T (CI) ∧v ∈V \ T (CI). If I(v).left ≤CI.right,
either I(v).right < CI.left or I(v) ⊃CI, since v̸ ∈T (CI).
For both two cases, I(v).left ≤CI.left, considering that
I(u).right ≥CI.left since u ∈T (CI), the edge (u, v) can-
not be a forward-cross edge since I(u).right ≥I(v).left.
For the case (iii), the condition (i) in the theorem guar-
antees that there is no forward-cross edge (u, v) in Tnew
such that u ∈V \ T (CI) ∧v ∈T (CI). On the one hand, if
I(u).left > CI.right or I(u) ⊃CI, we will have I(u).right ≥
CI.right ≥I(v).left. Therefore, the edge (u, v) cannot be
a forward-cross edge. On the other hand, if I(u).right <
CI.left, we assume that there is a forward-cross edge (u, v)
in Tnew, then edge (u, v) in T may be a tree edge, forward
edge, backward edge, forward-cross edge, or backward-cross
edge.
Firstly, edge (u, v) cannot be a tree edge or for-
ward edge in T .
If so, we would have I(u) ⊃I(v), and
this contradicts I(u).right < CI.left. Secondly, edge (u, v)
cannot be a backward edge in T .
If so, it would be a
backward edge in Tnew too.
Speciﬁcally, u ∈T (r), and
u is visited before T [CI.left] during DFS. Following Algo-
rithm 3, we visit vertices in the preorder of T before visiting
T [CI.left]. Therefore, v is an ancestor of u in Tnew, and
edge (u, v) is a backward edge.
Thirdly, edge (u, v) can-
not be a backward-cross edge in T . If so, we would have
I(v).right < I(u).left < I(u).right < CI.left, and this
contradicts v ∈T (CI). Considering aforementioned condi-
tions, edge (u, v) must be a forward-cross edge in T . We
have that if edge (u, v) is not a forward-cross edge in T , it
will not be a forward-cross edge in Tnew under the condition
I(u).right < CI.left.
For the case (iv), the condition (i) in the theorem guar-
antees that there is no forward-cross edge (u, v) in Tnew
such that u ∈V \ T (CI) ∧v ∈V \ T (CI). Since the time
interval of a vertex not in T (CI) will not change during
Algorithm 2, if I(u).right ≥I(v).left in T , we will have
I(u).right ≥I(v).left in Tnew too.
146

## Page 6

v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
[1, 40]
[2, 7]
[3, 6]
[4, 5]
[8, 37]
[9, 10]
[11, 32]
[12, 31]
[13, 14]
[15, 28]
[16, 17]
[18, 27]
[19, 26]
[20, 25]
[21, 22]
[23, 24]
[29, 30]
[33, 36]
[34, 35]
[38, 39]
(a) Result of Algorithm 4
v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
[1, 40]
[2, 7]
[3, 6]
[4, 5]
[8, 37]
[9, 10]
[11, 32]
[12, 31]
[13, 14]
[15, 28]
[16, 17]
[18, 27]
[19, 26]
[20, 25]
[21, 22]
[23, 24]
[29, 30]
[33, 36]
[34, 35]
[38, 39]
(b) Result of Algorithm 6
Figure 3: The updated DFS-Tree for the inserted
edge (v8, v13) in the graph G.
Theorem 2. Given a directed graph G and a search span-
ning tree T of G, the running time of Algorithm 2 is bounded
by O(�
u∈T (CI)∪{r} dout(u)), where r is the LCA of all ver-
tices in T (CI).
#### 5.
#### IMPLEMENTATIONS
#### 5.1
#### Edge Insertion
We give the basic implementation for the edge insertion in
this subsection. The pseudocode is shown in Algorithm 4.
Algorithm 4: DFS-Insert
Input: a directed graph G, a DFS-Tree T of G and
an inserted edge (s, t) in G
Output: the updated DFS-Tree
1 insert (s, t) into G;
2 if I(s).right > I(t).left then return T ;
3 r ←LCA(s, t);
4 CI ←[I(s).right, I(r).right];
5 ts ←CI.left;
6 ConstrainedDFS(r);
7 return the updated DFS-Tree T ;
We do nothing and return the original tree if (s, t) is not
a forward-cross edge in line 2. We compute the LCA of s
and t as the search root of ConstrainedDFS() in line 3 and
set the candidate interval as [I(s).right, I(r).right] in line
4. ConstrainedDFS() is invoked in line 6. A running example
is given as follows.
Example 2. Given the directed graph G in Figure 1(a) and
its DFS-Tree T in Figure 1(b), the updated DFS-Tree Tnew
computed by Algorithm 4 for an inserted edge (v8, v13) is
shown in Figure 3(a). The LCA of v8 and v13 in the original
DFS-Tree T is v3. v3 is also the LCA of all black vertices,
which is supported by Lemma 2. According to Figure 2(b),
the candidate time interval CI is assigned by [18, 37]. The
vertices falling in the candidate time interval CI are marked
in black. The time intervals of vertices which do not belong
to T (CI) (white vertices) do not change in the algorithm.
Lemma 5. In Algorithm 4, there is no forward-cross edge
(u, v) in Tnew such that u ∈T (CI) and I(v).left > CI.right.
The correctness of Algorithm 4 is guaranteed by combin-
ing Theorem 1 and Lemma 5. We give the time complexity
of Algorithm 4 as follows.
Theorem 3. Given a directed graph G, a DFS-Tree T of G
and an inserted edge (s, t), the running time of Algorithm 4
is bounded by O(�
u∈T [I(s).right,I(r).right] dout(u)), where r
is the LCA of s and t.
v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
[1, 40]
[9, 10]
[11, 18]
[12, 17]
[13, 16]
[14, 15]
[19, 20]
[21, 32]
[22, 29]
[30, 31]
[23, 26]
[24, 25]
[27, 28]
[33, 36]
[34, 35]
[38, 39]
[8, 37]
[2, 7]
[3, 6]
[4, 5]
(a) Result of Algorithm 5
v10
후
v0
v1
v2
v3
v4
v5
v7
v6
v12
v8
v11
v9
v13
v14
v18
v15
v16
v17
[1, 40]
[9, 10]
[11, 18]
[12, 17]
[13, 16]
[14, 15]
[19, 20]
[21, 32]
[22, 29]
[30, 31]
[23, 26]
[24, 25]
[27, 28]
[33, 36]
[34, 35]
[38, 39]
[8, 37]
[2, 7]
[3, 6]
[4, 5]
(b) Result of Algorithm 8
Figure 4:
The updated DFS-Tree for the deleted
edge (v5, v6) in the graph G.
#### 5.2
#### Edge Deletion
We explain the basic implementation for the edge deletion
in this subsection. The pseudocode is shown in Algorithm 5.
The pseudocode is self-explanatory, so we omit the detailed
description here.
Algorithm 5: DFS-Delete
Input: a directed graph G, a DFS-Tree T of G and a
deleted edge (s, t) in G
Output: the updated DFS-Tree
1 delete (s, t) from G;
2 if (s, t) is not a tree edge then return T ;
3 γ ←the virtual root of the DFS-Tree T ;
4 CI ←[I(t).left, I(γ).right];
5 ts ←CI.left;
6 ConstrainedDFS(γ);
7 return the updated DFS-Tree T ;
Example 3. Given the directed graph G in Figure 1(a) and
its DFS-Tree T in Figure 1(b), the updated DFS-Tree Tnew
computed by Algorithm 5 for a deleted edge (v5, v6) is pre-
sented in Figure 4(a). According to Figure 2(b), the can-
didate time interval CI is assigned by [12, 40]. Similar to
Figure 3(a), the vertices falling in the candidate time inter-
val CI are marked in black, and the time intervals of vertices
which do not belong to T (CI) (white vertices) do not change
in the algorithm.
Lemma 6. In Algorithm 5, there is no forward-cross edge
(u, v) in Tnew such that u ∈T (CI) and I(v).left > CI.right.
The correctness of Algorithm 5 is guaranteed by combin-
ing Theorem 1 and Lemma 6. We give the time complexity
of Algorithm 5 as follows.
Theorem 4. Given a directed graph G, a DFS-Tree T of G
and a deleted edge (s, t), the running time of Algorithm 5 is
bounded by O(�
u∈T [I(t).left,I(γ).right] dout(u)), where γ is
the virtual root of T .
#### 6.
#### THE IMPROVED APPROACHES
Drawbacks of Basic Solutions. Even though Algorithm 4
and Algorithm 5 correctly update the DFS-Tree, there is still
much room for improvement. First, the key step in both Al-
gorithm 4 and Algorithm 5 is to set a candidate time interval
CI. This interval can be very large, and many vertices will
consequently be visited in ConstrainedDFS(). Second, all the
out-neighbors of each discovered vertex will be scanned in
ConstrainedDFS(). The total number of their out-neighbors
can be very large especially in big graphs.
147

## Page 7

We propose several optimizations to improve the algorith-
mic eﬃciency.
In response to the drawbacks of the basic
solutions, we ﬁrst adopt a strategy which dynamically re-
ﬁnes the candidate time interval CI. Speciﬁcally, we con-
tinuously adjust the candidate interval in the process of the
algorithm, and the candidate interval is theoretically guar-
anteed to be never larger than that of the basic solutions.
In addition, we design a hybrid approach to perform the
constrained DFS. By hybrid, we mean searching vertices by
combining the graph search and the tree search. This avoids
scanning all the out-neighbors of the visited vertices in the
basic solutions. We introduce the details for edge insertion
and deletion in Section 6.1 and Section 6.2 respectively.
#### 6.1
#### Edge Insertion
6.1.1
Tightening Candidate Interval
We ﬁrst give some key observations for tightening the can-
didate interval in the edge insertion algorithm.
Lemma 7. Given an inserted edge (s, t), let C be the set of
new descendants of s in Algorithm 4, i.e. C = (Tnew(s) \
{s}) ∩T (CI), we have C = Tnew(t).
Lemma 8. Given an inserted edge (s, t), let w be the vertex
in Tnew(t) with the largest old right interval value, i.e., w =
arg maxv∈Tnew(t) I(v).right.
There is no edge (u, v) such
that u ∈Tnew(t) and I(v).left > I(w).right.
Example 4. Consider the graph G in Figure 1(a), the orig-
inal DFS-Tree T in Figure 1(b), and the updated DFS-Tree
Tnew in Figure 3(a) for an inserted edge (v8, v13). The new
descendants of v8 is C = Tnew(v13) = {v11, v12, v13, v14, v15}.
v12 has the largest old right interval value 32 as shown in
Figure 2(b).
The set of vertices with a left time interval
larger than 32 is {v16, v17, v18}, and there is no edge from
the vertex in Tnew(v13) to the vertex in this set.
Based on Lemma 8, we can use [I(s).right, I(w).right] as
the new candidate interval and guarantee the algorithmic
correctness. To derive I(w).right, we dynamically update
the candidate interval in the process of the edge insertion
algorithm. Speciﬁcally, given an inserted edge (s, t), we can
initialize the candidate interval as T [I(s).right, I(t).right]
since t must be in Tnew(t). Every time a new vertex v is as-
signed as a descendant of t, we update CI.right to I(v).right
if I(v).right > CI.right. The candidate interval stops up-
dating once all the descendants of t are collected in the up-
dated DFS-Tree Tnew. The following lemma shows that the
search space of this new candidate interval is at most the
same as that of Algorithm 4 in the worst case.
Lemma 9. Given an inserted edge (s, t), let w be the vertex
deﬁned in Lemma 8. I(w).right ≤I(r).right, where r is
the LCA of s and t.
6.1.2
From Graph Search to Tree Search
We further improve the algorithmic eﬃciency by replacing
a part of the graph search with tree search.
Lemma 10. Given an inserted edge (s, t) in Algorithm 4,
when ﬁnishing the visit of vertex t, i.e., u = t in line 12 of
Algorithm 3, there is no forward-cross edge in the graph.
Based on Lemma 10, at the ﬁnish moment of vertex t,
the tree is a valid DFS-Tree, and what we need is to update
the time intervals of the remaining vertices. Therefore, we
can simply search the tree instead of the graph to ﬁnish the
update. We give an example to explain Lemma 10.
Example 5. We continue to use Figure 3(a) for the inserted
edge (v8, v13). When all the descendants of v13 are collected
(the timestamp is 27), there is no forward-cross edge. At this
moment, all remaining vertices still in the candidate interval
are {v3, v5, v6, v8, v10}. Compared with Figure 2(b), the tree
structures of these remaining vertices do not change, and we
only update their time intervals.
6.1.3
The Overall Algorithm
By combining these two optimization techniques men-
tioned above, we detail our ﬁnal algorithm for edge insertion
in this subsection.
The pseudocode is presented in Algo-
rithm 6.
Algorithm 6: DFS-Insert∗
Input: a directed graph G, a DFS-Tree T of G and
an inserted edge (s, t) in G
Output: the updated DFS-Tree
1 insert (s, t) into G;
2 if I(s).right > I(t).left then return T ;
3 r ←LCA(s, t);
4 CI ←[I(s).right, I(t).right];
5 reassign t to the last element in C(s);
6 ts ←CI.left;
7 InsHybrid-DFS(r, t);
8 return the updated DFS-Tree T ;
Algorithm 7: InsHybrid-DFS(u, t)
1 mark u as visited;
2 if I(u).left ≥CI.left then
3
I(v).left ←ts, ts ←ts + 1;
4 if u ∈T (t) then
// Graph Search
5
C(u) = ∅;
6
foreach v ∈Nout(u):
I(v) ∩CI̸ = ∅∧I(v)̸ ⊃CI ∧v is unvisited do
7
reassign v to the last element in C(u);
8
CI.right ←max(CI.right, I(v).right);
9
InsHybrid-DFS(v, t);
10 else
// Tree Search
11
foreach v ∈C(u): I(v) ∩CI̸ = ∅do
12
InsHybrid-DFS(v, t);
13 if I(u).right ≤CI.right then
14
I(u).right ←ts, ts ←ts + 1;
In line 4 of Algorithm 6, we initialize the candidate in-
terval as [I(s).right, I(t).right]. We invoke the subroutine
named InsHybrid-DFS instead of ConstrainedDFS, and the
search root is still the LCA of s and t.
The pseudocode of InsHybrid-DFS is presented in Algo-
rithm 7. Similar to Algorithm 3, we update the left time
interval of u in lines 2–3 and the right time interval of u in
lines 13–14 respectively if necessary. We check whether u is
in T (t) in line 4. If yes, we perform the graph search in lines
5–9. The constraint (line 6) in the graph search is set to be
the same as that in line 4 of Algorithm 3. In line 8, we up-
date the right bound of the candidate interval if necessary.
If u is not in T (t), we perform the tree search in lines 11–
12. Line 11 guarantees that only the vertices falling in the
candidate interval are visited. We give a running example
of Algorithm 6 as follows.
148

## Page 8

Example 6. Given directed graph G in Figure 1(a) and its
DFS-Tree T
in Figure 1(b), the updated DFS-Tree Tnew
computed by Algorithm 6 for the inserted edge (v8, v13) is
shown in Figure 3(b).
For each visited vertex, if a graph
search is performed, the vertex is marked in black, or if a
tree search is performed, the vertex is marked in gray. Con-
sider the tree in Figure 3(a) derived by Algorithm 4. The
candidate interval is [18, 37], and there are 12 (black) ver-
tices visited in the algorithm, whereas in Figure 3(b), the
ﬁnal stable candidate interval is [18, 32]. Only 10 (black and
gray) vertices are visited in the algorithm, and we only visit
the tree children instead of the graph out-neighbors of the 5
(gray) vertices inside.
Theorem 5. Given a directed graph G, a DFS-Tree T of G
and an inserted edge (s, t), the running time of Algorithm 6
is O(|T [I(s).right, I(w).right]|+�
u∈Tnew(t) dout(u)), where
w is the vertex deﬁned in Lemma 8.
The left part of the complexity is the number of visited
vertices in the candidate interval [I(s).right, I(w).right],
and the right part is the number of out-neighbors of all
vertices in Tnew(t).
In brief, the left and right part rep-
resent the tree search and graph search in Algorithm 6 re-
spectively. Based on Lemma 9, the overall time complexity
of Algorithm 6 is not larger than that of Algorithm 4.
#### 6.2
#### Edge Deletion
In this subsection, we propose the optimizations for up-
dating the DFS-Tree when a tree edge is deleted.
6.2.1
A Similar Optimization to Edge Insertion
Recall that given a deleted tree edge (s, t) in Algorithm 5,
we straightforwardly append the subtree T (t) to the end of
the children list of the virtual root γ. This essentially trans-
forms the edge deletion problem to a forward-cross edge
repairing problem.
This method is ineﬃcient due to the
unpredictable generated forward-cross edges. A wide can-
didate interval (from I(t).left to I(γ).right) is set to cover
the possibly inﬂuenced vertices.
In order to tighten the candidate interval, one method is
to adopt a similar optimization in Section 6.1.1, which dy-
namically updates the candidate interval. Speciﬁcally, we
start the constrained DFS from the timestamp I(t).left,
i.e., CI.left = I(t).left, which is the same as that in Algo-
rithm 5, and do not limit the right bound of the candidate
interval initially. The DFS terminates immediately once all
the vertices in T (t) are visited.
However, the improvement of this optimization is limited
since the new ancestors of vertices in T (t) are unpredictable,
and we need to scan all the out-neighbors of every vertex
visited in the DFS.
6.2.2
Avoiding Unpredictable Graph Search
To improve the eﬃciency of the edge deletion, we adopt a
new method that iteratively appends the vertices in T (t) to
the tree as early as possible. For the vertices not in T (t), the
tree search is performed and the time interval is updated in
the tree. After visiting a special kind of vertex u which can
be the parent of vertices in T (t), we start the graph search
and collect a set of vertices in T (t) as the descendants of
u. The algorithm terminates once all vertices in T (t) are
appended to the tree. This new method further tightens the
candidate interval, and the graph search is only performed
on the vertices in T (t). We introduce the details below and
start by giving several deﬁnitions for ease of understanding.
Definition 4. (Local Earliest Visit Time) Given a ver-
tex u ∈T (t) and a vertex p ∈Nin(u) ∩(V \ T (t)), the local
earliest visit time of u regarding p, denoted by EVp(u), is the
smallest integer i such that i > I(p).left and ∄v ∈C(p) :
I(v).left < I(t).left ∧i ≤I(v).right.
Definition 5. (Earliest Visit Time and Potential
Parent) Given a vertex u ∈T (t), the earliest visit time of
u, denoted by EV(u), is the smallest local earliest visit time
of u, i.e., EV(u) = minp∈Nin(u)∩(V \T (t)) EVp(u). The cor-
responding vertex p of the minimum EVp(u) is the potential
parent of u, denoted by PP(u).
Note that due to the existence of virtual root γ, every
vertex in T (t) has a potential parent and earliest visit time.
The condition i > I(p).left guarantees that we visit u as
a child of p.
Given for any other child v ∈C(p), I(u) ∩
I(v) = ∅. The condition ∄v ∈C(p) : I(v).left < I(t).left ∧
i ≤I(v).right guarantees that i is the earliest position to
append u to C(p) after the timestamp I(t).left. We give an
example as follows.
Example 7. Reconsider the case of deleting the edge (v5, v6)
in the DFS-Tree shown in Figure 2. The vertex set in the
subtree T (v6) is {v6, v7, v8, v9, v10}. The vertex v8 has three
in-neighbors {v11, v14, γ} that are not in T (v6).
The lo-
cal earliest visit time EVv11(v8) is 23, EVv14(v8) is 28, and
EVγ(v8) is 38. Therefore, the potential parent of v8 is v11
and its earliest visit time is 23. In other words, the earliest
position to append v8 after the timestamp I(v6).left = 12
in the tree is the child of v11.
The vertex v10 has two in-neighbors {v3, γ} that are not
in T (v6). The local earliest visit time EVv3(v10) is 25, and
EVγ(v10) is 38. Thus, the potential parent of vertex v10 is
v3 and its earliest visit time is 25.
In this case, v10 can
be appended to C(v3) after v5, since v5 has been visited be-
fore I(v6).left = 12, and EV(v10) should be larger than
I(v5).right = 24.
Definition 6. (Trigger) Given a vertex set C ⊆T (t),
the trigger of C is a vertex u with the smallest earliest visit
time in C, i.e., u = arg minv∈C EV(v).
Note that it is possible that there are multiple triggers.
We break the tie by randomly selecting one in the algorithm.
An example to explain the above deﬁnitions is given below.
Example 8. Given the set C = T (v6), the trigger is v8. Its
earliest visit time and potential parent is 23 and v11 respec-
tively. For the other vertices in T (v6), we have PP(v10) =
v3, EV(v10) = 25 and PP(v6) = v13, EV(v6) = 27. The vir-
tual root γ is the only one in-neighbor not in T (v6) for the
vertices v7 and v9. We have PP(v7) = PP(v9) = γ and
EV(v7) = EV(v9) = 38.
We explain the rationale behind these deﬁnitions. Firstly,
we only allow the vertices in T (t) to append to the tree
after the timestamp I(t).left. This guarantees that there
is no new forward-cross edge (u, v) such that u ∈T (t) and
v is visited before I(t).left. Secondly, we ﬁnd the earliest
potential parent for each vertex in T (t), and this avoids
the appearance of forward-cross edges due to the backward
movement of vertices in T (t). We give examples as follows.
Example 9. Following the previous example, consider ver-
tex v7. The only in-neighbor of v7 not in T (v6) is γ. Ac-
cording to Deﬁnition 4 and Deﬁnition 5, the earliest po-
sition to append v7 is after v3.
If we omit the condition
∄v ∈C(p) : I(v).left < I(t).left ∧i ≤I(v).right in Deﬁni-
tion 4 and append v7 as the ﬁrst child of γ, this will generate
149

## Page 9

two new forward-cross edges (v7, v2) and (v7, v5). Therefore,
we only append vertices after the timestamp I(t).left.
On the other hand, consider vertex v8. There are three in-
neighbors not in T (v6), v11, v14 and γ. v11 is the potential
parent. If we append v8 to C(v14), it will generate a new
forward-cross edge (v11, v8).
Based on Deﬁnition 4, Deﬁnition 5 and Deﬁnition 6, we
compute the ﬁrst trigger u and its potential parent p by
scanning the in-neighbors of T (t). We compute the earliest
visit time of u and append u to the children list of p ac-
cordingly. We perform the tree search and update the time
intervals starting from the timestamp I(t).left. Once visit-
ing the trigger, we perform the graph search and collect its
all descendants. Note that for each trigger, only the vertices
in T (t) are appended to its new subtree. Once all descen-
dants of the trigger are collected, we locate the next trigger
and repeat this step. We terminate the procedure once all
vertices in T (t) are visited. The following subsection gives
a detailed algorithm and corresponding analysis.
6.2.3
The Overall Algorithm
We give our ﬁnal algorithm for edge deletion in this sub-
section. The pseudocode is presented in Algorithm 8.
Algorithm 8: DFS-Delete∗
Input: a directed graph G, a DFS-Tree T of G and a
deleted edge (s, t) in G
Output: the updated DFS-Tree
1 delete (s, t) from G;
2 if (s, t) is a non-tree edge then return T ;
3 delete t from C(s);
4 Vc ←T (t);
5 CI ←[I(t).left, +∞];
6 ts ←CI.left;
7 LocateNextTrigger();
8 while Vc is not empty do DelHybrid-DFS(r);
9 return the updated DFS-Tree T ;
Algorithm 9: LocateNextTrigger()
1 trigger ←get trigger in Vc based on Deﬁnition 6;
2 p ←PP(trigger);
3 v ←T [EV(trigger) −1];
4 if v = p then
5
reassign trigger to the ﬁrst element in C(p);
6 else
7
reassign trigger to the next element of v in C(p);
8 if r is undeﬁned then r ←LCA(s, p);
9 else r ←LCA(r, p);
We mark all candidate vertices as Vc in line 4. The left
bound of the candidate interval is initialized as I(t).left in
line 5, and the search will start from this timestamp. We do
not set the right bound since the algorithm will terminate
once all vertices in Vc are visited. We compute the trigger in
line 7 before performing the search and continuously invoke
the DelHybrid-DFS() until Vc is empty. The pseudocode of
LocateNextTrigger() and DelHybrid-DFS() are given in Algo-
rithm 9 and Algorithm 10 respectively.
In Algorithm 9, we ﬁrst compute the trigger in Vc in line
1. Based on Deﬁnition 4 and Deﬁnition 5, we reassign the
trigger to its earliest visit position in the children list of its
potential parent from line 2 to line 7. Similar to the previous
algorithms, r is the search entrance for the DelHybrid-DFS()
and is initialized by the LCA of s and p (line 8). Note that
unlike the previous methods, we dynamically update r, since
we compute a new trigger in each invocation of Algorithm 9.
The search entrance r must update to cover the new trigger
and guarantee the correctness (line 9).
Algorithm 10: DelHybrid-DFS(u)
1 mark u as visited;
2 if I(u).left ≥CI.left ∨u ∈Vc then
3
I(u).left ←ts, ts ←ts + 1;
4 if u ∈Vc then
// Graph Search
5
Vc ←Vc \ {u};
6
C(u) = ∅;
7
foreach v ∈Nout(u): v ∈Vc ∧v is unvisited do
8
reassign v to the last element in C(u);
9
DelHybrid-DFS(v);
10 else
// Tree Search
11
foreach v ∈C(u): I(v) ∩CI̸ = ∅∨v ∈Vc do
12
DelHybrid-DFS(v);
13
if v = trigger then
14
if Vc is empty then
15
CI.right ←ts −1;
16
else
17
LocateNextTrigger();
18 if I(u).right ≤CI.right then
19
I(u).right ←ts, ts ←ts + 1;
20
CI.left ←ts;
In Algorithm 10, we ﬁrst update the left time interval of
u if u falls in the candidate interval or u ∈Vc in lines 2–
3. Note that even though CI.left is initialized by I(t).left
and I(u).left ≥CI.left for all u ∈Vc holds at the begin-
ning, we update CI.left in the algorithm. Thus, condition
u ∈Vc is necessary.
The graph search is performed only
for the vertices in Vc and is shown in lines 4–9. In line 7,
we limit u’s out-neighbors to those belonging to Vc. This is
because we postpone visiting u and an out-neighbor v̸ ∈Vc
must be visited before.
Otherwise, the edge (u, v) would
be a forward-cross edge. The tree search is shown in lines
11–17. In line 13, if v is a trigger, a set of vertices has been
appended to the subtree of v. If Vc is empty, we actually
ﬁnish updating the DFS-Tree, and the algorithm can termi-
nate immediately. By setting CI.right as ts −1, no vertex
will be further visited. When Vc is not empty, we invoke
LocateNextTrigger() to ﬁnd the next earliest position and
complete the DFS-Tree. In line 18, all visited vertices sat-
isfy this condition until we set CI.right as ts−1. We update
the right time interval of u in line 19. Note that line 20 is an
important step to avoid visiting the same vertices repeatedly
and to guarantee the algorithmic correctness. Speciﬁcally,
recall that r updates in Algorithm 9. Let rold be the old one,
and rnew be the updated value. Assume that rnew is an an-
cestor of rold. In the invocation of DelHybrid-DFS(rnew), we
need to avoid searching the subtree T (rold) since the new
intervals of the vertices inside have been allocated in the
invocation of DelHybrid-DFS(rold). In this case, CI.left has
been updated to I(rold).right+1. We give a running exam-
ple for Algorithm 8 as follows.
150

## Page 10

Example 10. Given the directed graph G in Figure 1(a)
and its DFS-Tree T in Figure 1(b), the updated DFS-Tree
Tnew computed by Algorithm 8 for the deleted edge (v5, v6)
is shown in Figure 4(b).
Similar to the example of edge
insertion, each visited vertex is marked in black if the graph
search has been performed, and each visited vertex is marked
in gray if a tree search has been performed. The visited vertex
set is the union of the black and gray vertices.
Figure 4(a) derived by Algorithm 5 visits 16 (black) ver-
tices.
Figure 4(b) only visits 10 vertices.
The initial left
bound of the candidate interval in Algorithm 8 is I(v6).left =
12, and the right bound when terminating the algorithm is
26. Of these 10 vertices, we visit the tree children instead of
the graph out-neighbors for the 5 vertices.
Theorem 6. Given a directed graph G, a DFS-Tree T of G
and a deleted edge (s, t), the running time of Algorithm 8
is bounded by O(|C| + �
u∈T (t) d(u)), where |C| is the num-
ber of vertices visited in the candidate interval and d(u) =
din(u) + dout(u).
#### 6.3
#### Batch Update
Our proposed algorithms can be easily extended to handle
the batch update. Without loss of generality, a batch update
can be considered as a group of edge insertions followed by
a group of edge deletions.
Edge Insertion.
We assume that all the inserted edges
are forward-cross edges. For other kinds of edges, we always
ﬁrst add them into the graph since they will never break
the validity of the DFS-Tree. We denote the set of inserted
forward-cross edges as B+ = {(s1, t1), (s2, t2), ..., (sb, tb)}.
We set r = LCA(s1, t1, s2, t2, ..., sb, tb) and the candidate in-
terval CI = �
1≤i≤b [I(si).right, I(LCA(si, ti)).right] in the
batch update version of Algorithm 4. The optimization of
tightening the candidate interval discussed in Section 6.1.1
can also be applied in the batch insertion. Considering Al-
gorithm 6, besides the modiﬁcation of r in Algorithm 4, we
set CI = �
1≤i≤b [I(si).right, I(ti).right] and perform the
graph search in Algorithm 7 when ∃1 ≤i ≤b : u ∈T (ti) .
Edge Deletion. Similarly, we assume that all the deleted
edges are tree edges.
We denote the set of deleted tree
edges as B−= {(s1, t1), (s2, t2), ..., (sb, tb)}. We set CI =
[min1≤i≤b I(ti).left, I(γ).right] in the batch update version
of Algorithm 5. The optimizations discussed in Section 6.2.1
can also be applied in the batch deletion. Considering Al-
gorithm 8, besides the aforementioned modiﬁcations, we set
Vc = �
1≤i≤b T (ti).
#### 7.
#### EXPERIMENTS
We conducted extensive experiments to evaluate the per-
formance of our proposed algorithms. The algorithms eval-
uated in the experiments are summarized as follows:
• ReDFS-Insert and ReDFS-Delete: The naive methods are
discussed in Section 4. That is, Algorithm 1 is run if a
forward-cross edge is inserted or a tree edge is deleted.
• DFS-Insert and DFS-Delete: Algorithm 4 and Algorithm 5.
• DFS-Insert+ and DFS-Delete+: DFS-Insert+ represents Al-
gorithm 4 with the optimization of tightening the candi-
date interval discussed in Section 6.1.1. DFS-Delete+ rep-
resents Algorithm 5 with a similar optimization discussed
in Section 6.2.1.
• DFS-Insert∗and DFS-Delete∗: Algorithm 6 and Algorithm 8.
Table 2: Network Statistics
Dataset
|V |
|E|
|E|/|V |
CiteSeer
384,413
1,751,463
4.56
Web-Stanford
281,903
2,312,497
8.20
YahooAd
653,260
2,931,708
4.49
ProsperLoan
89,269
3,394,979
38.03
Wiki-Talk
2,394,385
5,021,410
2.10
Web-Google
875,713
5,105,039
5.83
Flickr
2,302,925
33,140,017
14.39
StackOverﬂow
2,601,977
63,497,050
24.40
LiveJournal
4,847,571
68,993,773
14.23
UK-2002
18,520,486
298,113,762
16.10
Wiki-Link
12,150,976
378,142,420
31.12
Twitter
41,652,230
1,468,365,182
35.25
All algorithms were implemented in C++ and compiled
using a g++ compiler at a -O3 optimization level. All the
experiments were conducted on a Linux Server with an Intel
Xeon 3.1GHz CPU and 128GB 1600MHz ECC DDR3-RAM.
Datasets. We conducted experiments on twelve publicly-
available real-world graphs and divided them into two groups
according to the data size.
Group one consists of six graphs with a relatively small
size.
Group two consists of six big graphs.
The detailed
statistics of these datasets are summarized in Table 2. All
networks and corresponding detailed descriptions can be
found in SNAP2, KONECT3, and WebGraph4.
Input Preparation. In order to test the performance of
our proposed algorithms, we randomly selected 10000 dis-
tinct existing edges in the graph for each test case.
For
edge deletion, we deleted these 10000 edges from the original
graphs one by one. For edge insertion, we started from the
graphs after removing these 10000 edges and corresponding
DFS-Tree. We inserted them into the graphs one by one.
For each algorithm, we calculated the average running time
for each edge insertion (resp. deletion).
The rest of this section is summarized as follows.
Sec-
tion 7.1 provides the overall processing time of all the four
algorithms. Then in Section 7.2, we evaluate the eﬀective-
ness of our proposed optimizations. Section 7.3 evaluates
the scalability. Section 7.4 reports the memory usage.
#### 7.1
#### Overall Efﬁciency
10-6
10-5
10-4
10-3
10-2
10-11
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Running Time (s)
ReDFS-Insert
DFS-Insert
DFS-Insert+
DFS-Insert*
(a) Small graphs
10-3
10-2
10-1
1
10
Flickr
StackOverflow LiveJournal
UK-2002
Wiki-Link
Twitter
Running Time (s)
(b) Big graphs
Figure 5: Running time for edge insertion
2http://snap.stanford.edu/data/index.html
3http://konect.uni-koblenz.de/networks/
4http://law.di.unimi.it/datasets.php
151

## Page 11

Edge Insertions. Figure 5 shows the running time of all
the four insertion algorithms on all datasets.
Based on
our proposed framework, DFS-Insert is more eﬃcient than
naively computing the DFS-Tree from scratch (ReDFS-Insert),
and our proposed optimization techniques further improve
the eﬃciency of DFS-Insert. For instance, the running time
of DFS-Insert∗on the smallest graph CiteSeer is 0.14ms.
Meanwhile, the running time of DFS-Insert+, DFS-Insert and
ReDFS-Insert is 0.39ms, 2.84ms and 5.40ms respectively
on the same dataset.
On the largest graph Twitter with
over 1 billion edges, DFS-Insert∗takes around 0.24s, while
DFS-Insert+, DFS-Insert and ReDFS-Insert takes about 1.06s,
1.19s and 6.75s respectively.
10-5
10-4
10-3
10-2
10-1
1
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Running Time (s)
ReDFS-Delete
DFS-Delete
DFS-Delete+
DFS-Delete*
(a) Small graphs
10-2
10-1
1
10
102
Flickr
StackOverflow LiveJournal
UK-2002
Wiki-Link
Twitter
Running Time (s)
(b) Big graphs
Figure 6: Running time for edge deletion
Edge Deletions. Figure 6 shows the running time of all
the four deletion algorithms on all datasets. Similar to Fig-
ure 5, we witness a large improvement from the baseline al-
gorithm to our ﬁnal algorithm. For example, on the small-
est graph CiteSeer, DFS-Delete∗takes only 0.14ms, while
DFS-Delete+, DFS-Delete and ReDFS-Delete take 0.44ms,
4.33ms and 5.75ms respectively. On the largest graph Twit-
ter, DFS-Delete∗takes approximately 1.79s, while the al-
gorithms DFS-Delete+, DFS-Delete and ReDFS-Delete take
around 8.78s, 9.45s and 10.27s respectively.
Table 3: Percentage of forward-cross edge insertions
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
7.64%
8.85%
6.95%
0.78%
Wiki-Talk
Web-Google
Flickr
StackOverﬂow
47.41%
9.55%
5.36%
2.61%
LiveJournal
UK-2002
Wiki-Link
Twitter
4.07%
4.24%
1.01%
1.89%
Table 4: Percentage of tree edge deletions
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
8.14%
11.5%
6.95%
1.07%
Wiki-Talk
Web-Google
Flickr
StackOverﬂow
47.73%
13.3%
6.52%
3.45%
LiveJournal
UK-2002
Wiki-Link
Twitter
6.46%
5.74%
1.92%
2.88%
Update Distribution. Recall that it only takes constant
time if the inserted edge is not a forward-cross edge or the
deleted edge is not a tree edge. To clearly show the perfor-
mance of our ﬁnal algorithm, we report the percentage of
10-4
10-2
1
102
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Flickr
StackOverflow
LiveJournal
UK-2002
Wiki-Link
Twitter
Running Time (s)
(a) Edge insertions
10-4
10-2
1
102
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Flickr
StackOverflow
LiveJournal
UK-2002
Wiki-Link
Twitter
Running Time (s)
(b) Edge deletions
Figure 7: Running time for tree updates
the forward-cross edge insertions (DFS-Insert∗) and the per-
centage of the tree edge deletions (DFS-Delete∗) in Table 3
and Table 4 respectively. We also report the average run-
ning time of DFS-Insert∗and DFS-Delete∗for these updates
in Figure 7 (a) and Figure 7(b) respectively.
#### 7.2
#### Effectiveness of Optimizations
We further evaluate the eﬀectiveness of our optimizations.
We count the number of ConstrainedDFS() invocations in
Algorithm 4 (resp. Algorithm 5) and denote it as cn. This
value represents the number of vertices performing graph
search in Algorithm 4 (resp. Algorithm 5). We also count
the numbers of vertices by graph search and tree search in
our ﬁnal algorithm respectively, which are denoted by cg
and ct. Speciﬁcally, for each invocation of InsHybrid-DFS()
in DFS-Insert∗(), we increase cg by one if it is true in line 4
of InsHybrid-DFS(). Otherwise, we increase ct by one. Simi-
larly, for edge deletion, we increase cg by one if it is true in
line 4 of DelHybrid-DFS(). Otherwise, we increase ct by one.
0
20%
40%
60%
80%
100%
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Flickr
StackOverflow
LiveJournal
UK-2002
Wiki-Link
Twitter
Percentage
Graph Search
Tree Search
(a) Edge insertions
0
20%
40%
60%
80%
100%
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Flickr
StackOverflow
LiveJournal
UK-2002
Wiki-Link
Twitter
Percentage
(b) Edge deletions
Figure 8: Percentage of vertices performing graph
search or tree search
#### 152

## Page 12

ReDFS-Insert
DFS-Insert
DFS-Insert+
DFS-Insert*
10-4
10-3
10-2
10-1
1
20%
40%
60%
80% 100%
Running Time (s)
(a) UK-2002 (Vary |V |)
10-2
10-1
1
10
20%
40%
60%
80% 100%
Running Time (s)
(b) Twitter (Vary |V |)
10-3
10-2
10-1
1
20%
40%
60%
80% 100%
Running Time (s)
(c) UK-2002 (Vary |E|)
10-1
1
10
20%
40%
60%
80% 100%
Running Time (s)
(d) Twitter (Vary |E|)
Figure 9: Scalability for edge insertion
ReDFS-Delete
DFS-Delete
DFS-Delete+
DFS-Delete*
10-4
10-3
10-2
10-1
1
20%
40%
60%
80% 100%
Running Time (s)
(a) UK-2002 (Vary |V |)
10-2
10-1
1
10
100
20%
40%
60%
80% 100%
Running Time (s)
(b) Twitter (Vary |V |)
10-3
10-2
10-1
1
20%
40%
60%
80% 100%
Running Time (s)
(c) UK-2002 (Vary |E|)
10-1
1
10
100
20%
40%
60%
80% 100%
Running Time (s)
(d) Twitter (Vary |E|)
Figure 10: Scalability for edge deletion
We report the value of ct/cn and cg/cn for both edge in-
sertion and deletion on all datasets in Figure 8. The black
part represents the ratio of visited vertices by the tree search
ct/cn, and the gray part represents the ratio of visited ver-
tices by the graph search cg/cn.
The results show that in our ﬁnal algorithms, the total
number of visited vertices is reduced on all datasets, and
there is a large proportion of tree search inside. Compared
with the basic algorithms for both operations, we only need
a very small number of graph searches. For example, the
largest percentage of graph search (i.e., cg/cn) for edge inser-
tion and deletion is about 17% and 23% on Twitter and Live-
Journal respectively. The lowest percentage is 0.000002% on
YahooAd for both edge insertion and deletion.
Overall, it is shown that our proposed optimization tech-
niques not only reduce the overall visited vertices but also
signiﬁcantly replace the out-neighbor search by the tree chil-
dren search.
#### 7.3
#### Scalability Test
This experiment tests the scalability of our proposed al-
gorithms. Due to the space limitation, we only report the
results for two real-world graph datasets as representatives
— UK-2002 and Twitter. The results on the other datasets
show similar trends. For each dataset, we vary the graph
size and graph density by randomly sampling vertices and
edges from 20% to 100%. When sampling vertices, we de-
rive the induced subgraph of the sampled vertices, and when
sampling edges, we select the incident vertices of the edges
as the vertex set.
The running time of DFS-Insert∗and DFS-Delete∗for edge
insertion and deletion of diﬀerent percentages is reported in
Figure 9 and Figure 10, respectively, with other algorithms
used as comparisons.
It can be seen that DFS-Insert∗and DFS-Delete∗perform
better than the other algorithms in all cases. For example,
considering edge insertion on UK-2002, the running time
of DFS-Insert∗, DFS-Insert+, DFS-Insert and ReDFS-Insert is
1.09ms, 2.48ms, 10.29ms and 19.79ms respectively when
sampling 20% vertices. When the sampling percentage of
vertices reaches 100%, DFS-Insert∗, DFS-Insert+, DFS-Insert
and ReDFS-Insert take about 18.30ms, 72.70ms, 74.26ms
and 203.22ms respectively.
Note that in Figure 9, the running time of several algo-
rithms on Twitter sightly decreases when the sampling ratio
increases in some cases. This is because in the 10000 update
operations, we do not need to update the tree structure if an
inserted edge is not a forward-cross edge or a deleted edge
is not a tree edge. The proportion of the operations that
lead to the tree update may be low in a large graph, so the
average processing time for each operation may be small.
#### 7.4
#### Memory Usage
Figure 11 shows the memory usage of all the four algo-
rithms on all datasets. We do not use any auxiliary data
structure in the ﬁnal algorithm. Therefore, the memory us-
age of all the proposed algorithms is same.
100M
1G
10G
100G
1TB
CiteSeer
Web-Stanford
YahooAd
ProsperLoan
Wiki-Talk
Web-Google
Flickr
StackOverflow
LiveJournal
UK-2002
Wiki-Link
Twitter
Memory Usage
Figure 11: Memory usage
#### 8.
#### CONCLUSIONS
This paper introduces a framework and corresponding al-
gorithms for the DFS-Tree maintenance problem considering
both edge insertion and deletion in general directed graphs.
Two groups of optimizations are also presented to speed up
the algorithms. The results of extensive performance stud-
ies demonstrate the eﬃciency of our proposed algorithms.
Based on the studies in this work, several possible research
problems have opened. We have given a basic idea to handle
the batch update in Section 6.3. A possible direction is to
further improve the eﬃciency of the batch update. Another
direction is to explore a vertex order and a corresponding
DFS-Tree to reduce the update cost.
#### 9.
#### ACKNOWLEDGEMENTS
Lu Qin is supported by ARC DP160101513. Ying Zhang is
supported by ARC FT170100128 and DP180103096. Xuemin
Lin is supported by 2018YFB1003504, 2019DH0ZX01, NSFC-
61232006, ARC DP180103096 and DP170101628.
153

## Page 13

#### 10.
#### REFERENCES
[1] S. Baswana, S. R. Chaudhury, K. Choudhary, and
S. Khan. Dynamic DFS in undirected graphs:
breaking the O(m) barrier. In Proceedings of the
twenty-seventh Annual ACM-SIAM Symposium on
Discrete Algorithms, pages 730–739. SIAM, 2016.
[2] S. Baswana and K. Choudhary. On dynamic DFS tree
in directed graphs. In International Symposium on
Mathematical Foundations of Computer Science, pages
102–114. Springer, 2015.
[3] S. Baswana, A. Goel, and S. Khan. Incremental DFS
algorithms: a theoretical and experimental study. In
Proceedings of the Twenty-Ninth Annual ACM-SIAM
Symposium on Discrete Algorithms, pages 53–72.
SIAM, 2018.
[4] S. Baswana, S. K. Gupta, and A. Tulsyan. Fault
tolerant and fully dynamic DFS in undirected graphs:
simple yet eﬃcient. arXiv preprint arXiv:1810.01726,
2018.
[5] L. Chen, R. Duan, R. Wang, and H. Zhang. Improved
algorithms for maintaining DFS tree in undirected
graphs. CoRR, abs/1607.04913, 2016.
[6] L. Chen, R. Duan, R. Wang, H. Zhang, and T. Zhang.
An improved algorithm for incremental DFS tree in
undirected graphs. In 16th Scandinavian Symposium
and Workshops on Algorithm Theory, 2018.
[7] T. H. Cormen, C. E. Leiserson, R. L. Rivest, and
C. Stein. Introduction to algorithms. MIT press, 2009.
[8] H. De Fraysseix, P. O. De Mendez, and P. Rosenstiehl.
Trémaux trees and planarity. International Journal of
Foundations of Computer Science, 17(05):1017–1029,
2006.
[9] E. W. Dijkstra. A discipline of programming.
Prentice-Hall series in automatic computation, 1976.
[10] P. G. Franciosa, G. Gambosi, and U. Nanni. The
incremental maintenance of a depth-ﬁrst-search tree in
directed acyclic graphs. Information processing letters,
61(2):113–120, 1997.
[11] J. Hopcroft and R. Tarjan. Algorithm 447: eﬃcient
algorithms for graph manipulation. Communications
of the ACM, 16(6):372–378, 1973.
[12] J. Hopcroft and R. Tarjan. Eﬃcient planarity testing.
Journal of the ACM (JACM), 21(4):549–568, 1974.
[13] P. B. Miltersen, S. Subramanian, J. S. Vitter, and
R. Tamassia. Complexity models for incremental
computation. Theoretical Computer Science,
130(1):203–236, 1994.
[14] K. Nakamura and K. Sadakane. A space-eﬃcient
algorithm for the dynamic DFS problem in undirected
graphs. In International Workshop on Algorithms and
Computation, pages 295–307. Springer, 2017.
[15] J. H. Reif. Depth-ﬁrst search is inherently sequential.
Information Processing Letters, 20(5):229–234, 1985.
[16] J. H. Reif. A topological approach to dynamic graph
connectivity. Information Processing Letters,
25(1):65–70, 1987.
[17] M. Sharir. A strong-connectivity algorithm and its
applications in data ﬂow analysis. Computers &
Mathematics with Applications, 7(1):67–72, 1981.
[18] J. F. Sibeyn, J. Abello, and U. Meyer. Heuristics for
semi-external depth ﬁrst search on directed graphs. In
Proceedings of the fourteenth annual ACM symposium
on Parallel algorithms and architectures, pages
282–292. ACM, 2002.
[19] J. Su, Q. Zhu, H. Wei, and J. X. Yu. Reachability
querying: can it be even faster? TKDE,
29(3):683–697, 2017.
[20] R. Tarjan. Depth-ﬁrst search and linear graph
algorithms. SIAM journal on computing, 1(2):146–160,
1972.
[21] R. E. Tarjan. A note on ﬁnding the bridges of a graph.
Inf. Process. Lett., 2:160–161, 1974.
[22] R. E. Tarjan. Edge-disjoint spanning trees and
depth-ﬁrst search. Acta Informatica, 6(2):171–185,
1976.
[23] A. Tucker. Chapter 2: covering circuits and graph
colorings. Applied Combinatorics, 49, 2006.
[24] H. Yildirim, V. Chaoji, and M. J. Zaki. Grail: scalable
reachability index for large graphs. PVLDB,
3(1):276–284, 2010.
154

---

## Extracted Tables


**Table (page 10):**

| Dataset | \|V \| | \|E\| | \|E\|/\|V \| |
| --- | --- | --- | --- |
| CiteSeer Web-Stanford YahooAd ProsperLoan Wiki-Talk Web-Google | 384,413 281,903 653,260 89,269 2,394,385 875,713 | 1,751,463 2,312,497 2,931,708 3,394,979 5,021,410 5,105,039 | 4.56 8.20 4.49 38.03 2.10 5.83 |
| Flickr StackOverflow LiveJournal UK-2002 Wiki-Link Twitter | 2,302,925 2,601,977 4,847,571 18,520,486 12,150,976 41,652,230 | 33,140,017 63,497,050 68,993,773 298,113,762 378,142,420 1,468,365,182 | 14.39 24.40 14.23 16.10 31.12 35.25 |


**Table (page 11):**

| CiteSeer Web-Stanford YahooAd ProsperLoan |  |  |  |
| --- | --- | --- | --- |
| 7.64% Wiki-Talk | 8.85% Web-Google | 6.95% Flickr | 0.78% StackOverflow |
| 47.41% | 9.55% | 5.36% | 2.61% |
| LiveJournal | UK-2002 | Wiki-Link | Twitter |
| 4.07% | 4.24% | 1.01% | 1.89% |


**Table (page 11):**

| CiteSeer | Web-Stanford | YahooAd | ProsperLoan |
| --- | --- | --- | --- |
| 8.14% | 11.5% | 6.95% | 1.07% |
| Wiki-Talk 47.73% | Web-Google 13.3% | Flickr 6.52% | StackOverflow 3.45% |
| LiveJournal | UK-2002 | Wiki-Link | Twitter |
| 6.46% | 5.74% | 1.92% | 2.88% |
