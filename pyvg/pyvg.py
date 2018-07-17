import sys
from pyvg.alignmentcollection import AlignmentCollection
from offsetbasedgraph import Graph


if sys.argv[1] == "create_alignment_collection":
    collection = AlignmentCollection(sys.argv[2], Graph.from_file(sys.argv[3]))