import json
import logging
from collections import defaultdict
import offsetbasedgraph as obg
from offsetbasedgraph import IntervalCollection
from .vgobjects import Graph, Alignment, Path, Mapping, Edit
import numpy as np

logger = logging.getLogger(__name__)

def get_json_lines(filename):

     with open(filename, "r") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.decoder.JSONDecodeError as e:
                logging.error("Fail when parsing vg json. Skipping this line and continuing: " + str(e) + "")
                continue
            except UnicodeDecodeError as e:
                logging.error("Unicode parsing fail when parsing vg json. Skipping this line and continuing: " + str(e) + "")
                continue



def get_json_paths_from_json(filename):
    with open(filename) as f:
        for line in f:
            try:
                yield json.loads(line)["path"] 
            except json.decoder.JSONDecodeError as e:
                logging.error("Fail when parsing vg path json. Skipping this line and continuing: " + str(e) + "")
                continue
            except KeyError as e:
                logging.error("Did not find path in alignment. Assuming this is mis-alignment: " + str(e) + "")


def parse_vg_json_alignments(mapping_file_name, ob_graph, include_score=False):
    json_objects = get_json_lines(mapping_file_name)
    alignments = (Alignment.from_json(json_object) for json_object in json_objects)
    
    if include_score:
        return ((alignment.name, alignment.path.to_obg_with_reversals(ob_graph),
                 alignment.score, alignment.mapq, alignment.refpos, alignment.chromosome) for alignment in alignments)

    return ((alignment.name, alignment.path.to_obg_with_reversals(ob_graph)) for alignment in alignments)


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

    # Find max and minh
    with open(json_file_name) as f:
        lines = f
        json_objs = (json.loads(line) for line in lines)
        has_warned_about_int = False
        for json_obj in json_objs:
            if "node" in json_obj:
                for node in json_obj["node"]:
                    id = node["id"]
                    if not isinstance(id, int):
                        if not has_warned_about_int:
                            logging.warning("Node id %s is not int. Converting to int when creating graph." % id)
                            has_warned_about_int = True
                        id = int(id) 

                    if id < min_node_id:
                        min_node_id = id

                    if id > max_node_id:
                        max_node_id = id

    logging.info("Min node: %d, Max node: %d" % (min_node_id, max_node_id))

    nodes = np.zeros((max_node_id - min_node_id) + 2, dtype=np.uint16)
    logging.info("Reading from json")
    with open(json_file_name) as f:
        lines = f
        json_objs = (json.loads(line) for line in lines)
        for json_obj in json_objs:
            if "node" in json_obj:
                for node in json_obj["node"]:
                    nodes[int(node["id"]) - min_node_id + 1] = len(node["sequence"])

            if "edge" in json_obj:
                for edge in json_obj["edge"]:

                    if "from_start" in edge and edge["from_start"] and "to_end" in edge and edge["to_end"]:
                        # new in vg 1.27, this is a normal edge from end to start
                        from_node = int(edge["to"])
                        to_node = int(edge["from"])
                        assert from_node >= 0 and to_node >= 0
                    else:
                        from_node = -int(edge["from"]) if "from_start" in edge and edge["from_start"] else edge["from"]
                        to_node = -int(edge["to"]) if "to_end" in edge and edge["to_end"] else edge["to"]
                    adj_list[int(from_node)].append(to_node)
                    rev_adj_list[-int(to_node)].append(-int(from_node))

    logging.info("Creating numpy adj lists")
    adj_list = obg.graph.AdjListAsNumpyArrays.create_from_edge_dict(adj_list)
    rev_adj_list = obg.graph.AdjListAsNumpyArrays.create_from_edge_dict(rev_adj_list)

    graph = obg.GraphWithReversals(nodes, adj_list,
                                  rev_adj_list=rev_adj_list,
                                  create_reverse_adj_list=False)
    graph.blocks.node_id_offset = min_node_id - 1
    return graph

