import json
import logging
import os
import pickle
from collections import defaultdict
import offsetbasedgraph
import stream
from pyvg import vg_pb2

class IntervalNotInGraphException(Exception):
    pass


class Position(object):
    def __init__(self, node_id, offset, is_reverse=False):
        self.node_id = node_id
        self.offset = offset
        self.is_reverse = is_reverse

    def __eq__(self, other):
        if self.node_id != other.node_id:
            return False
        if self.offset != other.offset:
            return False
        return self.is_reverse == other.is_reverse

    def __str__(self):
        return "Pos(%s, %s, %s)" % (self.node_id, self.offset, self.is_reverse)

    __repr__ = __str__

    def to_obg(self):
        return offsetbasedgraph.Position(self.node_id, self.offset)

    @classmethod
    def from_json(cls, position_dict):
        offset = int(position_dict["offset"]) if "offset" in position_dict else 0
        node_id = int(position_dict["node_id"])
        is_reverse = False
        if "is_reverse" in position_dict:
            is_reverse = position_dict["is_reverse"]
        return cls(node_id, offset, is_reverse)


class Edit(object):
    def __init__(self, to_length, from_length, sequence):
        self.to_length = to_length
        self.from_length = from_length
        self.sequence = sequence

    @classmethod
    def from_proto_obj(cls, obj):
        return cls(obj.to_length, obj.from_length, obj.sequence)

    def __eq__(self, other):
        attrs = ["to_length", "from_length", "sequence"]
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in attrs)

    def is_identity(self):
        return self.to_length == self.from_length and not self.sequence

    @classmethod
    def from_json(cls, edit_dict, skip_sequence=False):
        sequence = None
        if not skip_sequence:
            sequence = None if "sequence" not in edit_dict else edit_dict["sequence"]

        to_length = edit_dict["to_length"] if "to_length" in edit_dict else 0
        from_length = edit_dict["from_length"] if "from_length" in edit_dict else 0
        return cls(to_length, from_length, sequence)


class Mapping(object):
    def __init__(self, start_position, edits):
        self.start_position = start_position
        self.edits = edits

    def is_identity(self):
        return all(edit.is_identity() for edit in self.edits)

    def __eq__(self, other):
        attrs = ["start_position", "edits"]
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in attrs)

    def __str__(self):
        return "Map(%s, %s)" % (
            self.start_position, self.length())

    def node_id(self):
        if self.is_reverse():
            return -int(self.start_position.node_id)
        return int(self.start_position.node_id)

    def length(self):
        return sum(edit.from_length for edit in self.edits)

    def is_reverse(self):
        return self.start_position.is_reverse

    def get_start_offset(self):
        return self.start_position.offset

    def get_end_offset(self):
        start_offset = self.start_position.offset
        return start_offset + self.length()

    @classmethod
    def from_json(cls, mapping_dict):
        start_position = Position.from_json(mapping_dict["position"])

        edits = []
        if "edit" in mapping_dict:
            try:
                edits = [Edit.from_json(edit, skip_sequence=False) for edit in mapping_dict["edit"]]
            except KeyError:
                logging.error(mapping_dict)
                raise

        return cls(start_position, edits)


class Path(object):
    def __init__(self, name, mappings):
        self.mappings = mappings
        self.name = name

    def is_identity(self):
        return all(mapping.is_identity() for mapping in self.mappings)

    def __eq__(self, other):
        attrs = ["mappings"]
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in attrs)

    def __str__(self):
        return "Path[%s]" % ", ".join(
            str(mapping) for mapping in self.mappings)

    __repr__ = __str__

    def is_reverse(self):
        mapping_reverse = [mapping.is_reverse() for mapping in self.mappings]
        assert all(is_reverse == mapping_reverse[0] for is_reverse in mapping_reverse), mapping_reverse
        return mapping_reverse[0]

    @classmethod
    def from_json(cls, path_dict):
        name = path_dict["name"] if "name" in path_dict else None

        mappings = []
        if "mapping" in path_dict:
            mappings = [Mapping.from_json(mapping) for
                        mapping in path_dict["mapping"]]

        return cls(name, mappings)

    def to_obg_with_reversals(self, ob_graph=False):
        if len(self.mappings) == 0:
            return False

        start_offset = self.mappings[0].get_start_offset()
        end_offset = self.mappings[-1].get_end_offset()
        obg_blocks = [m.node_id() for m in self.mappings]

        interval = offsetbasedgraph.DirectedInterval(
            start_offset, end_offset,
            obg_blocks, ob_graph or None)

        if ob_graph:
            if not interval.length() == self.length():
                raise IntervalNotInGraphException("Interval %s is not valid interval in graph" % interval)

        return interval

    def length(self):
        return sum(mapping.length() for mapping in self.mappings)

    def to_obg(self, ob_graph=False):
        assert ob_graph is not None
        return self.to_obg_with_reversals(ob_graph=ob_graph)


class Node(object):
    def __init__(self, name, id, n_basepairs):
        self.name = name
        self.id = id
        self.n_basepairs = n_basepairs

    def __str__(self):
        return "Node(%s, %s)" % (self.id, self.n_basepairs)
    __repr__ = __str__

    @classmethod
    def from_json(cls, json_object):
        name = ""
        if "name" in json_object:
            name = json_object["name"]

        return cls(name, json_object["id"], len(json_object["sequence"]))

    def to_obg(self):
        return offsetbasedgraph.Block(self.n_basepairs)


class Edge(object):
    def __init__(self, from_node, to_node, from_start=False, to_end=False, overlap=0):
        self.from_node = from_node
        self.to_node = to_node
        self.from_start = int(from_start)
        self.to_end = int(to_end)
        self.overlap = int(overlap)

    @classmethod
    def from_json(cls, json_object):

        from_start = False
        to_end = False
        overlap = 0

        if "from_start" in json_object:
            from_start = json_object["from_start"]
            # Parsed by json == "True"  # NB: Is True correct?

        if "to_end" in json_object:
            to_end = json_object["to_end"]  # == "True"

        if "overlap" in json_object:
            overlap = int(json_object["overlap"])

        return cls(int(json_object["from"]),
                   int(json_object["to"]),
                   from_start,
                   to_end,
                   overlap,
                   )

    def get_from_node(self):
        if self.from_start:
            return -1*self.from_node
        return self.from_node

    def get_to_node(self):
        if self.to_end:
            return -1 * self.to_node
        return self.to_node


class Alignment(object):
    def __init__(self, path, identity, score=0, refpos=0, chromosome=None, mapq=0, name=None):
        self.identity = identity
        self.path = path
        self.score = score
        self.refpos = refpos
        self.chromosome = chromosome
        self.mapq = mapq
        self.name = name

    @classmethod
    def from_json(cls, alignment_dict):
        try:
            offset = int(alignment_dict["refpos"][0]["offset"])
            chromosome = alignment_dict["refpos"][0]["name"]
        except KeyError:
            logging.warning("Could not get offset from alignment. Defaulting to 0 instead.")
            offset = 0
            chromosome = None

        return cls(
            Path.from_json(alignment_dict["path"]),
            alignment_dict["identity"] if "identity" in alignment_dict else None,
            int(alignment_dict["score"]) if "score" in alignment_dict else None,
            offset,
            chromosome,
            int(alignment_dict["mapping_quality"]) if "mapping_quality" in alignment_dict else None,
            name=alignment_dict["name"] if "name" in alignment_dict else None
        )


class Snarls(object):
    def __init__(self, snarls):
        self.snarls = snarls

    @classmethod
    def from_vg_snarls_file(cls, vg_snarls_file_name):
        snarls = (snarl for snarl in
                  stream.parse(vg_snarls_file_name, vg_pb2.Snarl))
        return cls(snarls)


class ProtoGraph(object):
    """
    Holding a vg proto graph (restructured into list of nodes, edges and paths.
    Warning: Python proto reading is slow. Graph class reads from json and is faster.
    """

    def __init__(self, nodes, edges, paths):
        self.nodes = nodes
        self.edges = edges
        self.paths = paths

    @classmethod
    def from_vg_graph_file(cls, vg_graph_file_name, only_read_nodes=False,
                           use_cache_if_available=False):
        nodes = {}
        paths = []
        edges = []

        i = 0
        for line in stream.parse(vg_graph_file_name, vg_pb2.Graph):
            i += 1
            if hasattr(line, "node"):
                for node in line.node:

                    nodes[node.id] = node.sequence

            if only_read_nodes:
                continue

            if hasattr(line, "path"):
                for path in line.path:
                    paths.append(path)

            if hasattr(line, "edge"):
                for edge in line.edge:
                    assert edge.overlap == 0

        graph = cls(nodes, edges, paths)
        graph._cache_nodes()
        return graph

    @classmethod
    def from_node_dict(cls, node_dict):
        """Create a dummy object from a node dict (node id => sequence)"""
        return cls(node_dict, [], [])

    def _cache_nodes(self):
        with open("%s" % "vg_sequence_index.cached", "wb") as f:
            pickle.dump(self.nodes, f)


class Graph(object):

    def __init__(self, nodes, edges, paths):
        self.nodes = nodes
        self.edges = edges
        self.paths = paths
        self.node_dict = {node.id: node.n_basepairs for node in self.nodes}
        self.edge_dict = {}
        self.reverse_edge_dict = {}
        self._create_edge_dicts()

    @classmethod
    def from_file(cls, json_file_name, do_read_paths=True):
        logging.info("Reading vg graph from json file %s" % json_file_name)
        paths = []
        edges = []
        nodes = []
        f = open(json_file_name)
        lines = f.readlines()
        n_lines = len(lines)

        # object_types = ["Path", "Edge", "Node"]
        i = 1
        for line in lines:
            line = json.loads(line)
            i += 1

            if do_read_paths and "path" in line:
                paths.extend([Path.from_json(json_object) for json_object in line["path"]])
            if "node" in line:
                nodes.extend([Node.from_json(json_object) for json_object in line["node"]])
            if "edge" in line:
                edges.extend([Edge.from_json(json_object) for json_object in line["edge"]])

        obj = cls(nodes, edges, paths)
        if do_read_paths:
            obj.paths_as_intervals_by_chr = {}
        logging.info("Done reading vg graph")
        return obj

    def _create_edge_dicts(self):
        self.edge_dict = defaultdict(list)
        self.reverse_edge_dict = defaultdict(list)

        for edge in self.edges:
            self.edge_dict[edge.get_from_node()].append(edge.get_to_node())
            self.reverse_edge_dict[-edge.get_to_node()].append(-edge.get_from_node())

    def filter(self, objects):
        return [obj for obj in objects if self.is_in_graph(obj)]

    def edges_from_node(self, node_id):
        return self.edge_dict[node_id]

    def get_offset_based_graph(self):
        offset_based_edges = defaultdict(list)
        for edge in self.edges:
            from_node = edge.from_node
            to_node = edge.to_node
            if edge.from_start:
                from_node = -from_node
            if edge.to_end:
                to_node = -to_node

            offset_based_edges[from_node].append(to_node)

        offset_based_blocks = {}
        for block in self.nodes:
            offset_based_blocks[block.id] = block.to_obg()

        return offsetbasedgraph.GraphWithReversals(
            offset_based_blocks,
            offset_based_edges)
