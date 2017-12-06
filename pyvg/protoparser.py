from collections import defaultdict
import offsetbasedgraph as obg
import json
import stream
import vg_pb2
import cProfile
import logging


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


def json_file_to_obg_graph(json_file_name):
    logging.info("Creating ob graph from json file")
    nodes = {}
    adj_list = defaultdict(list)
    i = 0
    with open(json_file_name) as f:
        lines = f.readlines()
        json_objs = (json.loads(line) for line in lines)
        for json_obj in json_objs:
            if "node" in json_obj:
                for node in json_obj["node"]:
                    nodes[node["id"]] = obg.Block(len(node["sequence"]))
                    if i % 2 == 0:
                        logging.info("Node #%d" % i)
                    i += 1
            if "edge" in json_obj:
                for edge in json_obj["edge"]:
                    from_node = -edge["from"] if "from_start" in edge and edge["from_start"] else edge["from"]
                    to_node = -edge["to"] if "to_end" in edge and edge["to_end"] else edge["to"]
                    adj_list[from_node].append(to_node)
    return obg.GraphWithReversals(nodes, adj_list)


if __name__ == "__main__":
    # cProfile.run('proto_file_to_obg_graph("../../graph_peak_caller/tests/vgdata/haplo1kg50-mhc.vg")')
    cProfile.run('json_file_to_obg_graph("../../graph_peak_caller/tests/vgdata/haplo1kg50-mhc.json")')
