import json
from offsetbasedgraph import IntervalCollection

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
        vg_graph = vg.Graph.create_from_file(vg_json_file_name, False, chromosome)
        offset_based_graph = vg_graph.get_offset_based_graph()
        offset_based_graph.to_file(to_file_base_name + chromosome + ".tmp")


def vg_mapping_file_to_interval_list(vg_graph, vg_mapping_file_name, offset_based_graph=False):
    from pyvg import Alignment
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
        paths = vg_graph.filter([path])
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

def vg_mapping_file_to_interval_file(out_file_name, vg_graph, vg_mapping_file_name, offset_based_graph=False):
    interval_collection = IntervalCollection(
                vg_mapping_file_to_interval_list(vg_graph, vg_mapping_file_name, offset_based_graph))
    interval_collection.to_file(out_file_name)
    return out_file_name

if __name__ == "__main__":
    vg_to_offsetbasedgraphs_per_chromosome("../tests/x.json", "test_ofbg_")
