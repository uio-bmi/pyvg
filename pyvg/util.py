from .vg import Graph, Alignment, Path, Mapping
import json
import offsetbasedgraph
from offsetbasedgraph import IntervalCollection
import stream
import vg_pb2
from .sequences import SequenceRetriever


def get_interval_for_sequence_in_ob_graph(start_node_id, reference_file_name, ob_graph, vg_graph_file_name):

    offset = 0
    print("Reading sequences")
    reference_sequence = open(reference_file_name).read()
    current_node = start_node_id

    print("Getting sequence retriever")
    get_seq = SequenceRetriever.from_vg_graph(vg_graph_file_name).get_sequence_on_directed_node

    while current_node is not None:
        print("Current node: %d" % current_node)
        node_sequence = get_seq(current_node)
        current_ref_seq = reference_sequence[offset:offset + len(node_sequence)]
        #print("Node sequence: %s" % node_sequence[0:10])
        #print("Ref sequence: %s" % current_ref_seq[0:10])
        assert current_ref_seq == node_sequence

        offset += len(node_sequence)

        #print("Adjencies")
        #print(ob_graph.adj_list[current_node])
        candidates = {}
        max_length = 0
        next_node = None
        for next in ob_graph.adj_list[current_node]:
            next_sequence = get_seq(next)

            if next_sequence == reference_sequence[offset:offset+len(next_sequence)]:
                candidates[next] = next_sequence
                print(next_sequence)

        assert len(candidates) <= 2
        if len(candidates) > 1:
            print(candidates)
        #if len(candidates) > 0:
        #    next_node = list(candidates.keys())[0]

        max_length = 0
        for node, seq in candidates.items():
            if len(seq) > max_length:
                next_node = node
                max_length = len(seq)
                #print("Chose max as %d" % node)
        current_node = next_node

    print(offset)

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
        print("Creating graph for chromosome %s" % chromosome)
        vg_graph = Graph.create_from_file(vg_json_file_name, False, chromosome)
        offset_based_graph = vg_graph.get_offset_based_graph()
        offset_based_graph.to_file(to_file_base_name + chromosome + ".tmp")

def vg_mapping_file_to_interval_list(vg_graph, vg_mapping_file_name, offset_based_graph=False):
    if not offset_based_graph:
        print("Creating offsetbasedgraph")
        offset_based_graph = vg_graph.get_offset_based_graph()

    f = open(vg_mapping_file_name)
    jsons = (json.loads(line) for line in f.readlines())
    alignments =  []
    i = 0
    for json_dict in jsons:
        if "path" not in json_dict:  # Did not align
            #print("Alignment missing path")
            continue

        if i % 10000 == 0:
            print("Alignments processed: %d" % i)
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

    #paths = [alignment.path for alignment in alignments]
    #print("Filtering paths")
    #paths = vg_graph.filter(paths)   # Keep only the ones in graph
    #print("Translating")
    #obg_alignments = [path.to_obg(offset_based_graph) for path in paths]

    #return obg_alignments

def mapping_end_offset(mapping):
    start_offset = mapping.position.offset
    length = sum(edit.from_length for edit in mapping.edit)
    return start_offset + length

def path_is_reverse(path):
    if hasattr(path.mapping[0], "is_reverse"):
        if path.mapping[0].is_reverse:
            return True

    return False

def vg_gam_file_to_intervals(vg_graph, vg_mapping_file_name, offset_based_graph=False, max_intervals=False):
    import stream
    import vg_pb2

    i = 0
    for a in stream.parse(vg_mapping_file_name, vg_pb2.Alignment):
        path = a.path
        if i > 100000:
            print(path)

        try:
            obg_interval = vg_path_to_obg_interval(path, offset_based_graph)
        except Exception:
            print("Error with path")
            print(path)
            raise

        #print(obg_interval)
        if not obg_interval:
            continue

        if i % 1000 == 0:
            print("Interval # %d" % i)

        if(all([mapping.position.node_id in offset_based_graph.blocks for mapping in path.mapping])):
            if max_intervals:
                if i >= max_intervals:
                    return
            yield obg_interval
            i += 1


def vg_gam_file_to_interval_collection(vg_graph, vg_mapping_file_name, offset_based_graph=False, max_intervals=False):
    return offsetbasedgraph.IntervalCollection(
                vg_gam_file_to_intervals(vg_graph, vg_mapping_file_name, offset_based_graph=offset_based_graph, max_intervals=max_intervals)
            )

def vg_path_to_obg_interval(path, ob_graph = False):
    mappings = []
    for mapping in path.mapping:
        #edits = []
        #for edit in path.mapping.edits:
        #    edits.append(edit.to_length, edit.from_length, edit.sequence)

        obg_mapping = Mapping(mapping.position, mapping.edit)
        mappings.append(obg_mapping)

    path = Path(path.name, mappings)
    interval = path.to_obg_with_reversals(ob_graph)

    return interval

    if len(path.mapping) == 0:
        return False  # offsetbasedgraph.Interval(0, 0, [])

    nodes = [mapping.position.node_id for mapping in path.mapping]

    if path_is_reverse(path):
        if not ob_graph:
            raise Exception("Path is reverse and offset based graph is not sent")

        nodes = nodes[::-1]
        start_block_length = ob_graph.blocks[nodes[0]].length()
        start_offset = start_block_length - mapping_end_offset(path.mapping[-1])
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

    return offsetbasedgraph.Interval(
        start_offset, end_offset,
        nodes, interval_graph, direction=direction)


def vg_mapping_file_to_interval_file(out_file_name, vg_graph, vg_mapping_file_name, offset_based_graph=False):
    interval_collection = IntervalCollection(
                vg_mapping_file_to_interval_list(vg_graph, vg_mapping_file_name, offset_based_graph))
    interval_collection.to_file(out_file_name)
    return out_file_name


def vg_gam_file_to_gzip_interval_file(out_file_name, vg_graph, vg_mapping_file_name, offset_based_graph=False):
    interval_collection = IntervalCollection(
                vg_gam_file_to_intervals(vg_graph, vg_mapping_file_name, offset_based_graph))
    interval_collection.to_gzip(out_file_name)
    return out_file_name

if __name__ == "__main__":
    vg_to_offsetbasedgraphs_per_chromosome("../tests/x.json", "test_ofbg_")
