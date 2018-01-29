import cProfile
import json
import logging
from collections import defaultdict

import numpy as np
import offsetbasedgraph as obg
import stream

from pyvg import vg_pb2


def proto_file_to_obg_grpah(vg_graph_file_name):
    nodes = {}
    adj_list = defaultdict(list)
    for line in stream.parse(vg_graph_file_name, vg_pb2.Graph):
        if hasattr(line, "node"):
            for node in line.node:
                nodes[node.id] = obg.Block(len(node.sequence))
        if hasattr(line, "edge"):
            for edge in line.edge:
                from_node = -getattr(edge, "from") if edge.from_start else getattr(edge, "from")
                to_node = -edge.to if edge.to_end else edge.to
                adj_list[from_node].append(to_node)
    return obg.GraphWithReversals(nodes, adj_list)

#@profile
def json_file_to_obg_graph(json_file_name, n_nodes = 0):
    logging.info("Creating ob graph from json file")
    nodes = {}
    # assert n_nodes > 0
    #nodes = np.zeros(n_nodes+1, dtype=np.uint8)
    adj_list = defaultdict(list)
    rev_adj_list = defaultdict(list)

    i = 0
    with open(json_file_name) as f:
        lines = f.readlines()
        json_objs = (json.loads(line) for line in lines)
        for json_obj in json_objs:
            if "node" in json_obj:
                for node in json_obj["node"]:
                    nodes[node["id"]] = obg.Block(len(node["sequence"]))
                    #nodes[node["id"]] = len(node["sequence"])
                    #if i % 10000 == 0:
                    #    logging.info("Node #%d" % i)
                    #i += 1
            if "edge" in json_obj:
                for edge in json_obj["edge"]:
                    from_node = -edge["from"] if "from_start" in edge and edge["from_start"] else edge["from"]
                    to_node = -edge["to"] if "to_end" in edge and edge["to_end"] else edge["to"]
                    adj_list[from_node].append(to_node)
                    rev_adj_list[-to_node].append(-from_node)

    return obg.GraphWithReversals(nodes, adj_list,
                                  rev_adj_list=rev_adj_list,
                                  create_reverse_adj_list=False)


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


if __name__ == "__main__":
    # cProfile.run('proto_file_to_obg_graph("../../graph_peak_caller/tests/vgdata/haplo1kg50-mhc.vg")')
    cProfile.run('json_file_to_obg_graph("../../graph_peak_caller/tests/vgdata/haplo1kg50-mhc.json")')
