import offsetbasedgraph as obg
from pyvg.sequences import SequenceRetriever
from pyvg.vg import ProtoGraph
from pyvg.util import get_interval_for_sequence_in_ob_graph
# Find start nodes
import pyvg
from offsetbasedgraph.graphtraverser import GraphTraverserUsingSequence
from pybedtools import BedTool
#vg_graph = ProtoGraph.from_vg_graph_file("tests/cactus-mhc.vg", False, False)

"""
vg_py_graph = pyvg.Graph.create_from_file("tests/cactus-mhc.json")
ob_graph = vg_py_graph.get_offset_based_graph()
ob_graph.to_file("cactus-mhc.obg")
"""


ob_graph = obg.GraphWithReversals.from_file("cactus-mhc.obg")
#get_interval_for_sequence_in_ob_graph(1, "mhc_cleaned2.fa", ob_graph   , "tests/camel-mhc.vg")
search_sequence = open("mhc_cleaned2.fa").read()
sequence_retriever = SequenceRetriever.from_vg_graph("tests/cactus-mhc.vg")
traverser = GraphTraverserUsingSequence(ob_graph, search_sequence, sequence_retriever)
traverser.search_from_node(225518)
print(traverser.get_nodes_found())


ob_graph = obg.GraphWithReversals.from_file("cactus-mhc.obg")
search_sequence = open("mhc_cleaned2.fa").read()

bed_intervals_to_graph(ob_graph, linear_path_interval, "macs_peaks.bed", graph_start_offset=28510119)

"""
ob_graph = obg.GraphWithReversals.from_file("debruijn-mhc.obg")
start_nodes = ob_graph.get_first_blocks()

print(start_nodes)
print(len(start_nodes))
"""

"""
sequence_retriever = SequenceRetriever.from_vg_graph("tests/cactus-mhc.vg")
print(sequence_retriever.get_sequence_on_directed_node(1, 0))
"""