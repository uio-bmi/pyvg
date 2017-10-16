import offsetbasedgraph as obg
from pyvg.sequences import SequenceRetriever
from pyvg.vg import ProtoGraph
from pyvg.util import get_interval_for_sequence_in_ob_graph
# Find start nodes

#vg_graph = ProtoGraph.from_vg_graph_file("tests/cactus-mhc.vg", False, False)

ob_graph = obg.GraphWithReversals.from_file("obgraph")
get_interval_for_sequence_in_ob_graph(225518, "mhc_cleaned2.fa", ob_graph, "tests/cactus-mhc.vg")

"""
ob_graph = obg.GraphWithReversals.from_file("obgraph")
start_nodes = ob_graph.get_first_blocks()

print(start_nodes)

sequence_retriever = SequenceRetriever.from_vg_graph("tests/cactus-mhc.vg")
print(sequence_retriever.get_sequence_on_directed_node(1, 0))
"""