import json
import logging
from collections import defaultdict
import offsetbasedgraph as obg
from offsetbasedgraph import IntervalCollection
from .vgobjects import Graph, Alignment, Path, Mapping, Edit
import numpy as np

logger = logging.getLogger(__name__)


def get_json_paths_from_json(filename):
    with open(filename) as f:
        out = (json.loads(line)["path"] for line in f.readlines())
    return out


def vg_json_file_to_intervals(mapping_file_name, ob_graph=None, filter_funcs=()):
    logging.info("Initing json reads as generator from: %s" % mapping_file_name)
    json_paths = get_json_paths_from_json(mapping_file_name)
    paths = (Path.from_json(json_path) for json_path in json_paths)
    paths = (path for path in paths if
             all(filter_func(path) for filter_func in filter_funcs))

    intervals = (path.to_obg_with_reversals(ob_graph) for path in paths)
    return (i for i in intervals if i is not False)


def vg_json_file_to_interval_collection(vg_mapping_file_name, offset_based_graph=None):
    return obg.IntervalCollection(vg_json_file_to_intervals(vg_mapping_file_name, offset_based_graph))


def json_file_to_obg_numpy_graph(json_file_name, n_nodes = 0):
    """
    Faster method not using Graph class. Directly converts to a
    numpy-backed Offset Based Graph.
    """

    logging.info("Creating ob graph from json file")
    adj_list = defaultdict(list)
    rev_adj_list = defaultdict(list)
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
                    rev_adj_list[-to_node].append(-from_node)

    logging.info("Creating numpy adj lists")
    adj_list = obg.graph.AdjListAsNumpyArrays.create_from_edge_dict(adj_list)
    rev_adj_list = obg.graph.AdjListAsNumpyArrays.create_from_edge_dict(rev_adj_list)

    graph = obg.GraphWithReversals(nodes, adj_list,
                                  rev_adj_list=rev_adj_list,
                                  create_reverse_adj_list=False)
    graph.blocks.node_id_offset = min_node_id - 1
    return graph

