import logging
from .vg import Graph, Alignment, Path, Mapping, Edit
import json
import offsetbasedgraph
from offsetbasedgraph import IntervalCollection
from .sequences import SequenceRetriever
logger = logging.getLogger(__name__)
import numpy as np
from memory_profiler import profile


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


def get_chromosomes_from_vg_graph(vg_json_file_name):
    # TODO
    return ["chr3R", "chr3L", "chrX", "chrY", "chr4", "chr2R", "chr2L"]


def vg_to_offsetbasedgraphs_per_chromosome(vg_json_file_name, to_file_base_name = "offset_based_graph_"):
    """
    Parse the vg graph chromosome by chromosome, create one
    offsetbasedgraph per chromosome, and write to file.
    :param vg_json_file_name:
    :return:
    """
    for chromosome in get_chromosomes_from_vg_graph(vg_json_file_name):
        logger.info("Creating graph for chromosome %s" % chromosome)
        vg_graph = Graph.create_from_file(vg_json_file_name, False, chromosome)
        offset_based_graph = vg_graph.get_offset_based_graph()
        offset_based_graph.to_file(to_file_base_name + chromosome + ".tmp")


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

        #alignments.append(Alignment.from_json(json_dict))
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


def get_paths_from_gam(filename):
    import stream
    import vg_pb2
    return (alignment.path for alignment in
            stream.parse(filename,
                         vg_pb2.Alignment)
            if alignment.identity == 1.0)

#@profile
def get_json_paths_from_gam(filename):
    with open(filename) as f:
        out = (json.loads(line)["path"] for line in f.readlines())

    return out

def jsonpath_to_path(json_path):
    return Path.from_json(json_path)

def protopath_to_path(proto_path):
    mappings = [Mapping(mapping.position,
                        [Edit.from_proto_obj(e) for e in mapping.edit])
                for mapping in proto_path.mapping]

    return Path(proto_path.name, mappings)


def gam_file_to_intervals(vg_graph, mapping_file_name,
                          ob_graph, filter_funcs=()):
    logging.info("Getting alignments from: %s" % mapping_file_name)
    proto_paths = get_paths_from_gam(mapping_file_name)
    paths = (protopath_to_path(proto_path) for proto_path in proto_paths)
    paths = (path for path in paths if
             all(filter_func(path) for filter_func in filter_funcs))

    intervals = (path.to_obg_with_reversals(ob_graph) for path in paths)
    return (i for i in intervals if i is not False)

#@profile
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
    return offsetbasedgraph.IntervalCollection(
                vg_json_file_to_intervals(
                    vg_graph, vg_mapping_file_name,
                    offset_based_graph)
            )

def vg_gam_file_to_intervals(vg_graph, vg_mapping_file_name,
                             offset_based_graph=False,
                             max_intervals=False):

    def is_in_graph(path):
        #assert isinstance(offset_based_graph, offsetbasedgraph.GraphWithReversals)
        #assert all(isinstance(mapping.start_position.node_id, int) for mapping in path.mappings)
        is_in = (mapping.start_position.node_id in offset_based_graph.blocks
                   for mapping in path.mappings)
        #assert all(is_in)
        return all(is_in)
    intervals = gam_file_to_intervals(vg_graph, vg_mapping_file_name,
                                      offset_based_graph,
                                      [is_in_graph])
                                       #lambda path: path.is_identity()])
                                       #lambda path: np.random.randint(0, 6) == 1]

    return intervals


def vg_gam_file_to_interval_collection(
        vg_graph, vg_mapping_file_name,
        offset_based_graph=False, max_intervals=False):
    return offsetbasedgraph.IntervalCollection(
                vg_gam_file_to_intervals(
                    vg_graph, vg_mapping_file_name,
                    offset_based_graph=offset_based_graph,
                    max_intervals=max_intervals)
            )


def vg_gam_file_to_interval_list(vg_graph, vg_mapping_file_name,
                                 offset_based_graph=False,
                                 max_intervals=False):
    intervals = []
    collection = offsetbasedgraph.IntervalCollection(
                vg_gam_file_to_intervals(
                    vg_graph, vg_mapping_file_name,
                    offset_based_graph=offset_based_graph,
                    max_intervals=max_intervals)
            )
    for interval in collection:
        intervals.append(interval)

    return intervals


def vg_path_to_obg_interval(path, ob_graph=False):
    mappings = []
    for mapping in path.mapping:
        obg_mapping = Mapping(mapping.position, mapping.edit)
        mappings.append(obg_mapping)

    path = Path(path.name, mappings)
    interval = path.to_obg_with_reversals(ob_graph)
    return interval

    if len(path.mapping) == 0:
        return False

    nodes = [mapping.position.node_id for mapping in path.mapping]

    if path_is_reverse(path):
        if not ob_graph:
            raise Exception("Path is reverse and offset based graph is not sent")

        nodes = nodes[::-1]
        start_block_length = ob_graph.blocks[nodes[0]].length()
        start_offset = start_block_length - mapping_end_offset(
            path.mapping[-1])
        end_block_length = ob_graph.blocks[nodes[-1]].length()
        end_offset = end_block_length - mapping_end_offset(path.mapping[0])
        direction = -1
    else:
        start_offset = path.mapping[0].position.offset
        end_offset = mapping_end_offset(path.mapping[-1])
        direction = 1

    interval_graph = None
    if ob_graph:
        interval_graph = ob_graph
    interval = offsetbasedgraph.Interval(
        start_offset, end_offset,
        nodes, interval_graph, direction=direction)
    if end_offset == 0 or interval.end_offset == 0:
        print("#", path)
        print(interval)
        raise Exception("Endoffset == 0")
    print(interval)
    return interval


def vg_mapping_file_to_interval_file(out_file_name, vg_graph,
                                     vg_mapping_file_name,
                                     offset_based_graph=False):
    interval_collection = IntervalCollection(
                vg_mapping_file_to_interval_list(
                    vg_graph, vg_mapping_file_name, offset_based_graph))
    interval_collection.to_file(out_file_name)
    return out_file_name


def vg_gam_file_to_gzip_interval_file(out_file_name, vg_graph,
                                      vg_mapping_file_name,
                                      offset_based_graph=False):
    interval_collection = IntervalCollection(
                vg_gam_file_to_intervals(vg_graph, vg_mapping_file_name,
                                         offset_based_graph))
    interval_collection.to_gzip(out_file_name)
    return out_file_name

if __name__ == "__main__":
    vg_to_offsetbasedgraphs_per_chromosome("../tests/x.json", "test_ofbg_")
