import numpy as np
from .conversion import parse_vg_json_alignments
from collections import defaultdict
import pickle
import logging

logging.basicConfig(level=logging.DEBUG)

class AlignmentCollection:

    def __init__(self, node_dict, graph):
        self._node_dict = node_dict
        self._graph = graph

    @classmethod
    def from_vg_json_file(cls, file_name, ob_graph):
        alignments = parse_vg_json_alignments(file_name, ob_graph)

        node_dict = defaultdict(set)
        i = 0
        for name, interval in alignments:
            if i % 10000 == 0:
                logging.info("#%d processed" % i)

            for rp in interval.region_paths:
                node_dict[rp].add(name)
            i += 1

        return cls(node_dict, ob_graph)

    def to_file(self, file_name):
        with open(file_name, "wb") as f:
            pickle.dump(self._node_dict, f)

    @classmethod
    def from_file(cls, file_name, graph):
        logging.info("Writing to file")
        with open(file_name, "rb") as f:
            node_dict = pickle.load(f)
            return cls(node_dict, graph)


    def get_alignments_on_node(self, node_id):
        logging.info("Reading from file")
        return self._node_dict[node_id]

if __name__ == "__main__":
    import sys


    """"
    def __init__(self, ob_graph, alignment_names, index_sizes, node_to_alignment_mapppings):
        self.ob_graph = ob_graph
        self.alignment_names = alignment_names
        self.node_to_alignment_mappings = node_to_alignment_mapppings

    @classmethod
    def from_vg_json_file(cls, ob_graph, file_name):
         alignments =
    """


