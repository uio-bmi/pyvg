from offsetbasedgraph import NumpyIndexedInterval, Graph
import sys


def count_variants_in_graph(graph, linear_path):

    reference_nodes = linear_path.nodes_in_interval()
    n_variants = 0
    i = 0
    for node in graph.blocks:
        if i % 1000000 == 0:
            print("Node #%d" % i)
        i += 1
        if node not in reference_nodes:
            continue

        n_variants += max(0, len(graph.adj_list[node]) - 1)

    print("Variants: %d" % n_variants)
    return n_variants



if __name__ == "__main__":
    n_variants = 0
    for chromosome in sys.argv[2].split(","):
        print("Chromosome %s" % chromosome)
        graph = Graph.from_file(sys.argv[1] + "/" + chromosome + "_pruned.nobg")
        linear_path = NumpyIndexedInterval.from_file(sys.argv[1] + "/" + chromosome + "_linear_pathv2.interval")
        n_variants += count_variants_in_graph(graph, linear_path)

    print("Total: %d" % n_variants)