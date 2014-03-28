mctrain.py
==========
Author: Johan Gustafsson <johguse -human-test- student.chalmers.se>

A small command-line program used to generate graphs over railroad networks in
Minecraft worlds. It takes as input files in the Anvil file format (.mca) and
from these it generates output in .dot but also a basic .graphml version to
use with appropriate graphing tools.

This document in large roughly explains the work-flow of the program, to quickly
start using the program simply look to the usage examples in the section below.

Caching
-------
To reduce run-time for repeated runs over the same data-set the program can
cache the necessary data for a file for later use. You also have the option
for forcing the cache to be used in which case any changes to the Minecraft
world will not be reflected in the output. This option is best put to use when
testing various parameters.

How does it work
----------------
The program does two passes over the data it gathers. Before the first pass the
railroad network is represented as a graph where each node is a piece of
rail and an edge from the node represents a possible way to travel by minecart.

The program looks for nodes with only one edge, these are termed end-nodes.
These are fundamental to the graph that will be generated because they are in
essence a source and destination.

###First pass
During the first pass the program eliminates any nodes that are not used in the
shortest path between any pair of end-nodes. This process also identifies
strongly connected components in the graph and it discards any components which
are made up of too few nodes (i.e rail). This count can be set by using the
parameter ```--component-rail```. It defaults to 30, which should be sufficient to
filter out any rails present in mineshafts in the overworld.

Finally the program seeks to minimize the node count by eliminating any nodes
with only two edges such that:

A-B-C  -->  A-C

At this point there should only be two different kinds of nodes. Nodes with
only one edge which would be an end-node, and nodes with MORE than two edges
which are termed intersections. These are points at which rails intersects
in one way or another. Note that there's no data about which way a minecart
actually would travel in-game.

###Second pass
The second-pass is enabled by specifying a value for ```--distance-cluster```,
the recommended value is 40 (used in text below) but it is not set by default.

This pass works heuristically by combining end-nodes that are within the given
radius of each other. Note that this implies that two end-nodes A & B that
are seperated by 60 units CAN be combined into the same node if there's another
node C in between them such that A and C are within each others radius and C
and B also are within each others radius.

The resulting node that combines several end-nodes replaces them in the graph
and is positioned at the average position of all its constituents.

Such a node is referred to as a cluster-node. In the event that a generated
cluster-node only has one outgoing edge it will silently be downgraded to a
regular end-node (with the modified position). As such it is possible to
classify cluster-nodes as two different kinds. Those with only two edges and
those with more than two. These are termed switches and stations respectively.
Any cluster-node without an edge will be discarded.

The terms are logical consequences of the two cases. A clustered node with
only two edges means you will have to leave the minecart and switch to a new
rail to arrive at a destination, and you only have one option on where to
travel. As such, it's a simple switch. The location of the switch might also
be an intended destination, to treat it as such in the output use the flag
```--switch-as-endpoint```. If a switch becomes labeled by using the flag
```--distance-label``` it will also be treated as an endpoint.

Stations are termed as such due to its multitude of edges, i.e selections in
your destination.

After the cluster-nodes have been generated and replaced their end-nodes the
graph is once again minimized as described in the first pass, first by removing
nodes not used in the shortest path and then by removing any non-clustered nodes
with only two edges.

NOTE: The algorithm for the shortest path is actually only a breadth-first
search, and as such it only does an approximation.

###Drawing
The program does no drawing by itself it only generates graph files in the
formats .dot and .graphml. The former is mainly used in conjunction with
the graphviz toolset. For the second format, yEd is highly recommended.

It does however set some properties of the nodes that dictate their drawing.
Intersectons will be small black circular nodes. Switches are a bit larger
orange circular nodes. Stations are blue larger circular nodes and end-nodes
are drawn in green rectangles. By default, the position for stations and
end-points are used as their labels. Custom labels are explained in the next
section.

####DOT
The program was made with the DOT format in mind, and as such it has some
features which it only supports for the DOT format. If you wish to label
edges with the geometric distance it spans in integer, use ```--label-edges```.

If you wish to draw edges which are geometrically longer as thicker, use
```--edge-weight```. The recommended value is 4. By default it is off.

###Labels
The program can scan the Minecraft world for signs following a specific format.
If the sign is in close proximity of one of the final nodes in the graph as
specified by the option ```--distance-label``` then the second and third row of the
sign will be concatenated to form the label. New-lines can be inserted by
typing "\n" in the signs text. The first row of the sign must be "-MCTRAIN-"
without the quotes. The last row of the sign is reserved for future use.

###Components
By default the program outputs the whole graph to one file for each of the two
formats. The graph might contain several different components that would fit
to be rendered using different layouts. Specifying ```--component-divide``` as an
option will divide all strongly connected components in the graph into their
own respective file. The files are named mctrain-graph-<sequence number>.

Often there are many many components with only two end-nodes, to combine
these into one output-file, specify ```--combine-pairs```.

Some components might have most of its end-nodes geometrically close, even
though they're made up of enough rail to not be discarded in the first pass.

To discard any components where the largest distance between two end-nodes is
too small use the option ```--distance-min```.

We use this library on GitHub when rendering your README or any other
rich text file.

Usage examples
--------------
First time run, the folder myCacheFolder must exist:

```./mctrain.py --cache=myCacheFolder --distance-cluster=40 --component-rail=40
--component-divide --combine-pairs myMinecraft/myWorld/region/*.mca```

Re-running over the cached data trying different parameters:
```./mctrain.py --only-cache --cache=myCacheFolder --distance-cluster=60
--component-rail=30 myMinecraft/myWorld/region/*.mca```

Remember to remove any output-files left over from a previous run as to not
confuse it with freshly generated output.

Do not re-use the same cache for different worlds. Be it overworld, nether,
the-end etc.

Graphviz example
----------------
```sfdp -Goverlap=prism -Gsplines=curved -Nmargin=0.02
-Tpng mctrain-graph-0.dot > mctrain-graph-0.png```

[Example 1](https://raw.githubusercontent.com/johguse/mctrain/master/examples/graphviz_example1.png), [Example 2](https://raw.githubusercontent.com/johguse/mctrain/master/examples/graphviz_example2.png)

yEd example
-----------
The .graphml file that is output has the bare minimum data so as to be able to
be used in yEd. The nodes will be mal-sized and all centered on top of each
other. To fix this, do the following in yEd with the graph loaded:

Tools -> Fit Node To Label

There are many layouts you can use in yEd, my favorite is the orthogonal.

Layout -> Orthogonal -> Classic
* Grid: 5
* Minimum First Segment Length: 2.0
* Minimum Last Segment Length: 2.0
* Minimum Segment Length: 2.0
	
[Example 1](https://raw.githubusercontent.com/johguse/mctrain/master/examples/yed_example_1.png)

Disclaimer
----------
I wrote this program mainly for my own personal use, as such you should not
have any expectations on the software.
