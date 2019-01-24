import numpy as np
from .conversion import parse_vg_json_alignments
from collections import defaultdict
import pickle
from offsetbasedgraph import IntervalCollection
import logging
from graph_peak_caller.intervals import UniqueIntervals

logging.basicConfig(level=logging.DEBUG)

class AlignmentCollection:

    def __init__(self, node_dict, graph, intervals):
        self._node_dict = node_dict
        self._graph = graph
        self.intervals = intervals

    @classmethod
    def from_vg_json_file(cls, file_name, ob_graph):
        alignments = parse_vg_json_alignments(file_name, ob_graph)
        intervals = []
        node_dict = defaultdict(set)
        i = 0
        for name, interval in alignments:
            if i % 10000 == 0:
                logging.info("#%d processed" % i)

            for rp in interval.region_paths:
                node_dict[rp].add((name, i))
            intervals.append(interval)
            i += 1
        

        return cls(node_dict, ob_graph, intervals)

    def to_file(self, file_name):
        logging.info("Writing to file")
        with open(file_name, "wb") as f:
            pickle.dump(self._node_dict, f)

        IntervalCollection(self.intervals).to_file(file_name + ".intervals")
        
    @classmethod
    def from_file(cls, file_name, graph):
        logging.info("Reading from file")
        logging.info("Reading dict structure")
        with open(file_name, "rb") as f:
            node_dict = pickle.load(f)

        logging.info("Reading intervals")
        intervals = IntervalCollection.from_file(file_name + ".intervals", graph=graph)
        return cls(node_dict, graph, list(intervals))

    def get_alignments_on_node(self, node_id):
        return {name: self.intervals[index] for name, index in self._node_dict[node_id]}

    def get_alignments_on_interval(self, interval):
        alignments = {}
        for node in interval.region_paths:
            alignments.update(self.get_alignments_on_node(node))
            alignments.update(self.get_alignments_on_node(-node))

        return alignments

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


