import offsetbasedgraph as obg
from pyvg.sequences import SequenceRetriever
from pyvg.vg import ProtoGraph
from pyvg.util import get_interval_for_sequence_in_ob_graph
# Find start nodes
import pyvg

#vg_graph = ProtoGraph.from_vg_graph_file("tests/cactus-mhc.vg", False, False)

"""
vg_py_graph = pyvg.Graph.create_from_file("debruijn-mhc-k31.json")
ob_graph = vg_py_graph.get_offset_based_graph()
ob_graph.to_file("debruijn-mhc.obg")
"""

"""
ob_graph = obg.GraphWithReversals.from_file("camel-mhc.obg")
get_interval_for_sequence_in_ob_graph(1, "mhc_cleaned2.fa", ob_graph   , "tests/camel-mhc.vg")
"""

ob_graph = obg.GraphWithReversals.from_file("debruijn-mhc.obg")
start_nodes = ob_graph.get_first_blocks()

print(start_nodes)
print(len(start_nodes))


"""
sequence_retriever = SequenceRetriever.from_vg_graph("tests/cactus-mhc.vg")
print(sequence_retriever.get_sequence_on_directed_node(1, 0))
"""