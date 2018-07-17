import sys
from pyvg.alignmentcollection import AlignmentCollection
from offsetbasedgraph import Graph
import logging


if sys.argv[1] == "create_alignment_collection":
    collection = AlignmentCollection.from_vg_json_file(sys.argv[2], Graph.from_file(sys.argv[3]))
    collection.to_file(sys.argv[4])
    logging.info("Wrote to file %s" % sys.argv[4])
