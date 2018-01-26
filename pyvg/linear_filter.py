from util import get_paths_from_gam
import offsetbasedgraph as obg


def graph_to_indexed_interval(graph):
    pass


class LinearFilter:
    def __init__(self, position_tuples, indexed_intervals):
        self._nodes = set()
        for indexed_interval in indexed_intervals.values():
            self._nodes.update(indexed_interval.region_paths)

        self._position_tuples = position_tuples

    def find_chrm(self, node):
        for chrom, nodes in self._nodes.items():
            if node in nodes:
                return chrom, "+"
            if -node in nodes:
                return chrom, "-"
        return None, None

    def find_start_positions(self):
        dicts = {"+": {key: [] for key in self._nodes.keys()},
                 "-": {key: [] for key in self._nodes.keys()}}

        for pos in self._positions:
            chrom, direction = self.find_chrm(position.region_path_id)
            if chrom is None:
                continue
            indexed_interval = self._indexed_intervals[chrom]
            dicts[direction][chrom] = indexed_interval.get_offset_at_position(
                pos, direction)

        chroms = (self.find_chrm(pos) for pos in self._position_tuples)

    @classmethod
    def from_gam_and_graphs(cls, gam_file_name, graphs):
        paths = get_paths_from_gam(gam_file_name)
        positions = (path.position for path in paths)
        positions = (obg.Position(-position.node_id,
                                  position.offset)
                     if position.is_reverse else
                     obg.Position(position.node_id,
                                  position.offset)
                     for position in positions)
        indexed_intervals = [
            graph_to_indexed_interval(graph) for graph in graphs]
        return cls(positions, indexed_intervals)
