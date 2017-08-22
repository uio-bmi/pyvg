import vg

def get_chromosomes_from_vg_graph(vg_json_file_name):
    # TODO: Fiz
    return ["chr4", "chr2R", "chr2L"]


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


if __name__ == "__main__":
    vg_to_offsetbasedgraphs_per_chromosome("../tests/x.json", "test_ofbg_")







