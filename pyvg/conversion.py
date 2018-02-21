import json
import logging
from collections import defaultdict
import offsetbasedgraph as obg
from offsetbasedgraph import IntervalCollection
from .sequences import SequenceRetriever
from .vgobjects import Graph, Alignment, Path, Mapping, Edit

logger = logging.getLogger(__name__)


def vg_mapping_file_to_interval_list(vg_graph, vg_mapping_file_name, offset_based_graph=False):
    if not offset_based_graph:
        logger.info("Creating offsetbasedgraph")
        offset_based_graph = vg_graph.get_offset_based_graph()

    f = open(vg_mapping_file_name)
    jsons = (json.loads(line) for line in f.readlines())
    alignments =  []
    i = 0
    for json_dict in jsons:
        if "path" not in json_dict:  # Did not align
            continue

        if i % 10000 == 0:
            logger.info("Alignments processed: %d" % i)
        i += 1

        alignment = Alignment.from_json(json_dict)
        path = alignment.path
        if vg_graph:
            paths = vg_graph.filter([path])
        else:
            paths = [path]

        if len(paths) > 0:
            obg_interval = path.to_obg(offset_based_graph)
            obg_interval.graph = offset_based_graph
            yield obg_interval


def mapping_end_offset(mapping):
    start_offset = mapping.position.offset
    length = sum(edit.from_length for edit in mapping.edit)
    return start_offset + length


def path_is_reverse(path):
    if hasattr(path.mapping[0], "is_reverse"):
        if path.mapping[0].is_reverse:
            return True

    return False

def jsonpath_to_path(json_path):
    return Path.from_json(json_path)


def protopath_to_path(proto_path):
    mappings = [Mapping(mapping.position,
                        [Edit.from_proto_obj(e) for e in mapping.edit])
                for mapping in proto_path.mapping]

    return Path(proto_path.name, mappings)


def get_json_paths_from_gam(filename):
    with open(filename) as f:
        out = (json.loads(line)["path"] for line in f.readlines())

    return out


def vg_json_file_to_intervals(vg_graph, mapping_file_name,
                          ob_graph=None, filter_funcs=()):
    logging.info("Getting json reads from: %s" % mapping_file_name)
    json_paths = get_json_paths_from_gam(mapping_file_name)
    paths = (jsonpath_to_path(json_path) for json_path in json_paths)
    paths = (path for path in paths if
             all(filter_func(path) for filter_func in filter_funcs))

    intervals = (path.to_obg_with_reversals(ob_graph) for path in paths)
    return (i for i in intervals if i is not False)


def vg_json_file_to_interval_collection(vg_graph, vg_mapping_file_name, offset_based_graph=None):
    return obg.IntervalCollection(
                vg_json_file_to_intervals(
                    vg_graph, vg_mapping_file_name,
                    offset_based_graph)
            )

def vg_path_to_obg_interval(path, ob_graph=False):
    mappings = []
    for mapping in path.mapping:
        obg_mapping = Mapping(mapping.position, mapping.edit)
        mappings.append(obg_mapping)

    path = Path(path.name, mappings)
    interval = path.to_obg_with_reversals(ob_graph)
    return interval

def vg_mapping_file_to_interval_file(out_file_name, vg_graph,
                                     vg_mapping_file_name,
                                     offset_based_graph=False):
    interval_collection = IntervalCollection(
                vg_mapping_file_to_interval_list(
                    vg_graph, vg_mapping_file_name, offset_based_graph))
    interval_collection.to_file(out_file_name)
    return out_file_name

def json_file_to_obg_numpy_graph(json_file_name, n_nodes = 0):
    logging.info("Creating ob graph from json file")
    nodes = {}
    node_ids = []


    adj_list = defaultdict(list)
    #adj_list = obg.graphwithreversals.AdjList()
    rev_adj_list = defaultdict(list)
    #rev_adj_list = obg.graphwithreversals.AdjList()
    i = 0

    min_node_id = 1e15
    max_node_id = 0

    # Find max and min
    with open(json_file_name) as f:
        lines = f.readlines()
        json_objs = (json.loads(line) for line in lines)
        for json_obj in json_objs:
            if "node" in json_obj:
                for node in json_obj["node"]:
                    id = node["id"]
                    if id < min_node_id:
                        min_node_id = id

                    if id > max_node_id:
                        max_node_id = id

    logging.info("Min node: %d, Max node: %d" % (min_node_id, max_node_id))

    nodes = np.zeros((max_node_id - min_node_id) + 2, dtype=np.uint16)
    #adj_list = obg.graph.AdjListAsMatrix(max_node_id + 1)
    logging.info("Reading from json")
    with open(json_file_name) as f:
        lines = f.readlines()
        json_objs = (json.loads(line) for line in lines)
        for json_obj in json_objs:
            if "node" in json_obj:
                for node in json_obj["node"]:
                    nodes[node["id"] - min_node_id + 1] = len(node["sequence"])

            if "edge" in json_obj:
                for edge in json_obj["edge"]:
                    from_node = -edge["from"] if "from_start" in edge and edge["from_start"] else edge["from"]
                    to_node = -edge["to"] if "to_end" in edge and edge["to_end"] else edge["to"]
                    adj_list[from_node].append(to_node)
                    #adj_list.add_edge(from_node, to_node)
                    rev_adj_list[-to_node].append(-from_node)

    logging.info("Creating numpy adj lists")
    adj_list = obg.graph.AdjListAsNumpyArrays.create_from_edge_dict(adj_list)
    rev_adj_list = obg.graph.AdjListAsNumpyArrays.create_from_edge_dict(rev_adj_list)

    graph = obg.GraphWithReversals(nodes, adj_list,
                                  rev_adj_list=rev_adj_list,
                                  create_reverse_adj_list=False)
    graph.blocks.node_id_offset = min_node_id - 1
    return graph


def get_interval_for_sequence_in_ob_graph(start_node_id, reference_file_name,
                                          ob_graph, vg_graph_file_name):
    offset = 0
    logger.info("Reading sequences")
    reference_sequence = open(reference_file_name).read()
    current_node = start_node_id

    logger.info("Getting sequence retriever")
    get_seq = SequenceRetriever.from_vg_graph(vg_graph_file_name).get_sequence_on_directed_node

    while current_node is not None:
        logger.debug("Current node: %d" % current_node)
        node_sequence = get_seq(current_node)
        current_ref_seq = reference_sequence[offset:offset + len(node_sequence)]
        assert current_ref_seq == node_sequence

        offset += len(node_sequence)
        candidates = {}
        max_length = 0
        next_node = None
        for next in ob_graph.adj_list[current_node]:
            next_sequence = get_seq(next)

            if next_sequence == reference_sequence[offset:offset+len(next_sequence)]:
                candidates[next] = next_sequence
                logger.debug(next_sequence)

        assert len(candidates) <= 2
        if len(candidates) > 1:
            logger.debug(candidates)

        max_length = 0
        for node, seq in candidates.items():
            if len(seq) > max_length:
                next_node = node
                max_length = len(seq)
        current_node = next_node

    logger.debug(offset)