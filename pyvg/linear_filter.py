from .util import vg_json_file_to_intervals
import offsetbasedgraph as obg


def graph_to_indexed_interval(graph):
    pass


class LinearFilter:
    def __init__(self, position_tuples, indexed_interval):
        self._nodes = set()
        self._nodes.update(indexed_interval.region_paths)
        self._position_tuples = position_tuples
        self._indexed_interval = indexed_interval

    def find_start_positions(self):
        start_positions = {"+": [],
                 "-": [] }

        for pos in self._position_tuples:
            direction = "+"
            if pos.node_id < 0:
                direction = "-"
            start_positions[direction].append(self._indexed_interval.get_offset_at_position(
                pos, direction))
        return start_positions

    @classmethod
    def from_vg_json_reads_and_graph(cls, json_file_name, graph_file_name):
        graph = obg.GraphWithReversals.from_unknown_file_format(graph_file_name)
        intervals =  vg_json_file_to_intervals(None, json_file_name, graph)
        positions = (interval.start_position for interval in intervals)

        indexed_interval = graph.get_indexed_interval_through_graph()
        return cls(positions, indexed_interval)

