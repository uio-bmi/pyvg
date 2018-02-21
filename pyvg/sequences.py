from .vgobjects import ProtoGraph
import json
import logging


class SequenceRetriever(object):
    _compliments = {"A": "T",
                    "C": "G",
                    "T": "A",
                    "G": "C"}

    def __init__(self, node_dict):
        self.nodes = node_dict

    def _reverse_compliment(self, sequenence):
        return "".join(self._compliments[c] for c in sequenence[::-1])

    @classmethod
    def from_vg_graph(cls, vg_graph_file_name):
        vg_graph = ProtoGraph.from_vg_graph_file(
            vg_graph_file_name, True, True)
        return cls(vg_graph.nodes)

    @classmethod
    def from_vg_json_graph(cls, vg_graph_file_name):
        node_dict = {}
        f = open(vg_graph_file_name)
        i = 1
        for line in f.readlines():
            line = json.loads(line)
            if "node" in line:
                node_objects = line["node"]
                for node_object in node_objects:
                    node_dict[node_object["id"]] = node_object["sequence"].lower()
                    i += 1
                    if i % 1000000 == 0:
                        logging.info("%d nodes processed" % i)

        return cls(node_dict)

    def get_sequence_on_directed_node(self, node_id, start=0, end=False):
        """Handles directed nodes"""
        if node_id > 0:
            return self.get_sequence(node_id, start, end)
        else:
            node_size = len(self.get_sequence(-node_id))

            if not end:
                end = node_size

            new_start = node_size - end
            new_end = node_size - start
            reverse_sequence = self.get_sequence(-node_id, new_start, new_end)
            return self._reverse_compliment(reverse_sequence)

    def get_sequence(self, node_id, start=0, end=False):
        assert node_id > 0
        nodes = self.nodes
        if start == 0 and not end:
            return nodes[node_id]
        elif not end:
            return nodes[node_id][start:]
        else:
            return nodes[node_id][start:end]

    def get_interval_sequence(self, interval):

        rps = interval.region_paths
        start_node = rps[0]
        end_node = rps[-1]

        if start_node == end_node and len(rps) == 1:
            return self.get_sequence_on_directed_node(
                start_node,
                interval.start_position.offset,
                interval.end_position.offset)
        else:

            start_sequence = self.get_sequence_on_directed_node(
                start_node,
                interval.start_position.offset)
            end_sequence = self.get_sequence_on_directed_node(
                end_node,
                0,
                interval.end_position.offset)
            middle_sequence = ""
            for rp in rps[1:-1]:
                middle_sequence += self.get_sequence_on_directed_node(rp)

            return "%s%s%s" % (start_sequence, middle_sequence, end_sequence)






