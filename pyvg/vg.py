import json
import offsetbasedgraph
from collections import defaultdict
import pickle
import os
import logging
import stream
import vg_pb2


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
        node_id = position_dict["node_id"]
        is_reverse = False
        if "is_reverse" in position_dict:
            is_reverse = position_dict["is_reverse"]
        return cls(node_id, offset, is_reverse)


class Edit(object):
    def __init__(self, to_length, from_length, sequence):
        self.to_length = to_length
        self.from_length = from_length
        self.sequence = sequence

    def __eq__(self, other):
        attrs = ["to_length", "from_length", "sequence"]
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in attrs)

    @classmethod
    def from_json(cls, edit_dict):
        sequence = None if "sequence" not in edit_dict else edit_dict["sequence"]
        to_length = edit_dict["to_length"] if "to_length" in edit_dict else 0
        from_length = edit_dict["from_length"] if "from_length" in edit_dict else 0
        return cls(to_length, from_length, sequence)


class Mapping(object):
    def __init__(self, start_position, edits):
        self.start_position = start_position
        self.edits = edits

    def __eq__(self, other):
        attrs = ["start_position", "edits"]
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in attrs)

    def __str__(self):
        return "Map(%s, %s)" % (
            self.start_position, sum(edit.to_length for edit in self.edits))

    def is_reverse(self):
        return self.start_position.is_reverse

    def get_start_offset(self):
        return self.start_position.offset

    def get_end_offset(self):
        start_offset = self.start_position.offset
        length = sum(edit.from_length for edit in self.edits)
        return start_offset + length

    @classmethod
    def from_json(cls, mapping_dict):
        start_position = Position.from_json(mapping_dict["position"])

        edits = []
        if "edit" in mapping_dict:
            try:
                edits = [Edit.from_json(edit) for edit in mapping_dict["edit"]]
            except KeyError:
                print(mapping_dict)
                raise

        return cls(start_position, edits)


class Path(object):
    def __init__(self, name, mappings):
        self.mappings = mappings
        self.name = name

    def __eq__(self, other):
        attrs = ["mappings"]
        return all(getattr(self, attr) == getattr(other, attr)
                   for attr in attrs)

    def __str__(self):
        return "Path[%s]" % ", ".join(str(mapping) for mapping in self.mappings)

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
            mappings = [Mapping.from_json(mapping) for mapping in path_dict["mapping"]]

        return cls(name, mappings)

    def to_obg_with_reversals(self, ob_graph=False):
        if len(self.mappings) == 0:
            return False # offsetbasedgraph.DirectedInterval(0, 0, [])

        obg_blocks = []
        start_offset = self.mappings[0].start_position.offset
        end_offset = self.mappings[-1].start_position.offset

        for mapping in self.mappings:
            position = mapping.start_position
            if mapping.is_reverse():
                node_id = -position.node_id
            else:
                node_id = position.node_id

            obg_blocks.append(node_id)

        interval_graph = None
        if ob_graph:
            interval_graph = ob_graph

        interval = offsetbasedgraph.DirectedInterval(
            start_offset, end_offset,
            obg_blocks, interval_graph)
        #print(interval)
        return interval


    def to_obg(self, ob_graph=False):
        return self.to_obg_with_reversals(ob_graph=ob_graph)

        if len(self.mappings) == 0:
            return offsetbasedgraph.Interval(0, 0, [])

        nodes = [mapping.start_position.node_id for mapping in self.mappings]

        if self.is_reverse():
            if not ob_graph:
                raise Exception("Path is reverse and offset based graph is not sent")

            nodes = nodes[::-1]
            start_block_length = ob_graph.blocks[nodes[0]].length()
            start_offset = start_block_length - self.mappings[-1].get_end_offset()
            end_block_length = ob_graph.blocks[nodes[-1]].length()
            end_offset = end_block_length - self.mappings[0].get_end_offset()
            direction = -1
        else:
            start_offset = self.mappings[0].get_start_offset()
            end_offset = self.mappings[-1].get_end_offset()
            direction = 1

        interval_graph = None
        if ob_graph:
            interval_graph = ob_graph

        return offsetbasedgraph.Interval(
            start_offset, end_offset,
            nodes, interval_graph, direction=direction)


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

        #print(json_object)
        #if json_object["from"] == 6510:
        #    print(json_object)

        if "from_start" in json_object:
            from_start = json_object["from_start"]
            # Parsed by json == "True"  # NB: Is True correct?

        if "to_end" in json_object:
            to_end = json_object["to_end"]  # == "True"

        if "overlap" in json_object:
            overlap = int(json_object["overlap"])

        return cls(json_object["from"],
                   json_object["to"],
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
    def __init__(self, path, identity):
        self.identity = identity
        self.path = path

    @classmethod
    def from_json(cls, alignment_dict):

        #print(alignment_dict)
        return cls(
            Path.from_json(alignment_dict["path"]),
            alignment_dict["identity"])


class AlignmentCollection(object):
    def __init__(self, alignments):
        self.alignments = alignments

    @classmethod
    def create_generator_from_file(cls, file_name):
        f = open(file_name)
        jsons = (json.loads(line) for line in f.readlines())
        alignments = (Alignment.from_json(json_dict) for json_dict in jsons)
        return cls(alignments)

    def __iter__(self):
        return self.alignments.__iter__()


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
    Holding a vg proto graph (restructured into list of nodes, edges and paths
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
    #@filecache(24*60*60)
    def create_from_file(cls, json_file_name, max_lines_to_read=False, limit_to_chromosomes=False, do_read_paths=True):
        paths = []
        edges = []
        nodes = []
        f = open(json_file_name)
        lines = f.readlines()
        n_lines = len(lines)
        print("Number of lines: %d" % n_lines)

        # object_types = ["Path", "Edge", "Node"]
        i = 0
        for line in lines:
            line = json.loads(line)
            if i % 100 == 0:
                print("Line: %d/%d" % (i, n_lines))
            i += 1
            if limit_to_chromosomes:
                if "path" not in line:
                    continue
                if line["path"][0]["name"] not in limit_to_chromosomes:
                    if len(nodes) > 0:
                        # Assuminng there are nothing more on this chromosome now
                        break

                    continue


            if do_read_paths and "path" in line:
                paths.extend([Path.from_json(json_object) for json_object in line["path"]])
            if "node" in line:
                nodes.extend([Node.from_json(json_object) for json_object in line["node"]])
            if "edge" in line:
                edges.extend([Edge.from_json(json_object) for json_object in line["edge"]])

            if max_lines_to_read and i >= max_lines_to_read:
                break


        obj = cls(nodes, edges, paths)
        if do_read_paths:
            obj.paths_as_intervals_by_chr = {}
            #obj._merge_paths_by_name()

        return obj

    @classmethod
    # TODO Not finished
    def create_from_proto_file(cls, proto_file_name, max_lines_to_read=False, limit_to_chromosome=False, do_read_paths=True):
        # todo
        paths = []
        edges = []
        nodes = []
        import stream
        import vg_pb2
        i = 0
        for line in stream.parse(proto_file_name, vg_pb2.Graph):

            print(line)
            if i % 100 == 0:
                print("Line: %d" % (i))

            i += 1

    def _create_edge_dicts(self):
        self.edge_dict = defaultdict(list)
        self.reverse_edge_dict = defaultdict(list)

        for edge in self.edges:
            self.edge_dict[edge.get_from_node()].append(edge.get_to_node())
            self.reverse_edge_dict[-edge.get_to_node()].append(-edge.get_from_node())

    def _interval_has_no_edges_in(self, interval):

        start_node = interval.region_paths[0]
        if abs(start_node) not in self.reverse_edge_dict:
            return True

        return False

        for edge in self.edges:
            if edge.to_node == interval.region_paths[0]:
                return False
        return True

    def is_in_graph(self, obj):
        if isinstance(obj, Position):
            return obj.node_id in self.node_dict
        elif isinstance(obj, Mapping):
            return self.is_in_graph(obj.start_position)
        elif isinstance(obj, Path):
            return all(self.is_in_graph(mapping) for mapping
                       in obj.mappings)
        elif isinstance(obj, Alignment):
            return self.is_in_graph(obj.path)
        assert False, type(obj)

    def filter(self, objects):
        return [obj for obj in objects if self.is_in_graph(obj)]

    def edges_from_node(self, node_id):

        return self.edge_dict[node_id]

        edges = []
        for edge in self.edges:
            if edge.from_node == node_id:
                edges.append(edge.to_node)

        return edges

    def _merge_paths_by_name(self):
        print("merging paths")
        # Join all paths with the same name
        paths_by_name = defaultdict(list)
        for path in self.paths:
            paths_by_name[path.name].append(path)

        for name in paths_by_name:
            print(name)
            intervals = []
            for path in paths_by_name[name]:
                intervals.append(path.to_obg())

            #if name == "chr4":
            #    print(intervals)

            # Create a single connectected interval for this name
            region_paths = []
            # Find the starting interval (no edges in)
            start_intervals = []
            for interval in intervals:
                if self._interval_has_no_edges_in(interval):
                    start_intervals.append(interval)
            assert len(start_intervals) == 1, print("\n\n".join([str(i.region_paths[0]) for i in intervals]))

            # Traverse to connect all intervals
            current_interval = start_intervals[0]
            start_position = current_interval.start_position
            number_of_intervals_added = 0
            while True:
                region_paths.extend(current_interval.region_paths)
                number_of_intervals_added += 1
                next_nodes = self.edges_from_node(current_interval.region_paths[-1])
                potential_next_intervals = []
                for potential_next_interval in intervals:
                    if potential_next_interval.region_paths[0] in next_nodes:
                        potential_next_intervals.append(potential_next_interval)

                assert len(potential_next_intervals) <= 1

                if len(potential_next_intervals) == 0:
                    break

                current_interval = potential_next_intervals[0]

            end_position = current_interval.end_position

            single_linear_interval = offsetbasedgraph.Interval(start_position, end_position, region_paths)
            assert number_of_intervals_added == len(intervals)
            #print(single_linear_interval)

            self.paths_as_intervals_by_chr[name] = single_linear_interval

    @classmethod
    def from_file(cls, file_name):
        """
        Load graph from pickle

        :param file_name: File name
        :rtype: Graph
        """
        if os.path.isfile("%s" % file_name):
            obj = pickle.load(open(file_name, "rb"))
            return cls(obj.nodes, obj.edges, obj.paths)
        else:
            print("Warning: Graph not found" % file_name)
            return None

    def to_file(self, file_name):
        """
        Writes the graph to file so that it later can be
        recreated using the from_file method

        :param file_name: File name
        :return:
        """
        with open("%s" % file_name, "wb") as f:
            pickle.dump(self, f)

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
        #print(offset_based_blocks)
        return offsetbasedgraph.GraphWithReversals(
            offset_based_blocks,
            offset_based_edges)

    def get_translation(self, limit_to_chromosome=False):
        offset_based_graph = self.get_offset_based_graph()

        trans_dict = {}
        trans_dict_reverse = defaultdict(list)

        for chromosome in self.paths_as_intervals_by_chr:
            if limit_to_chromosome and limit_to_chromosome != chromosome:
                print("Skipping %s" % chromosome)
                continue

            offset_based_graph_path = self.paths_as_intervals_by_chr[chromosome]
            offset_based_graph_path.graph = offset_based_graph
            trans_dict[chromosome] =  [offset_based_graph_path]

            # Create reverse dict
            offset = 0


            for block in offset_based_graph_path.region_paths:
                block_length = offset_based_graph.blocks[block].length()



                trans_dict_reverse[block] = [
                            offsetbasedgraph.Interval(offset, offset + block_length, [chromosome], None)]
                offset += block_length

        return offsetbasedgraph.Translation(trans_dict, trans_dict_reverse, offset_based_graph)


if __name__ == "__main__":

    f = open("./dm_test_data/mapped_reads_sample.json")
    jsons = (json.loads(line) for line in f.readlines())
    alignments = [Alignment.from_json(json_dict) for json_dict in jsons]
    for alignment in alignments:
        print(alignment.path.is_reverse(), alignment.path.to_obg())
