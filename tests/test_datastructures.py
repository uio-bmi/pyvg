from pyvg import Graph, Mapping, Alignment, Node, Edge, Snarls, Path
import unittest
from offsetbasedgraph import GraphWithReversals, Block
import json

def create_test_data():
    simple_graph = """
    {
    "node": [
        {"id": 1, "sequence": "TTTCCCC"},
        {"id": 2, "sequence": "TTTT"},
        {"id": 3, "sequence": "CCCCTTT"}
    ],
    "edge": [
        {"from": 1, "to": 2},
        {"from": 2, "to": 3, "to_end": true}
    ]
    }
    """

    f = open("simple_graph.json", "w")
    f.write(simple_graph.replace("\n", " "))
    f.close()


class TestGraph(unittest.TestCase):

    def test_graph_from_json(self):
        graph = Graph.from_file("simple_graph.json")
        self.assertEqual(len(graph.nodes), 3)
        self.assertEqual(graph.nodes[0].id, 1)
        self.assertEqual(graph.nodes[1].id, 2)
        self.assertEqual(graph.nodes[2].id, 3)
        self.assertEqual(graph.nodes[0].n_basepairs, 7)
        self.assertEqual(graph.nodes[1].n_basepairs, 4)
        self.assertEqual(graph.nodes[2].n_basepairs, 7)

        self.assertEqual(graph.edges[0].from_node, 1)
        self.assertEqual(graph.edges[0].to_node, 2)
        self.assertEqual(graph.edges[0].from_start, False)
        self.assertEqual(graph.edges[0].to_end, False)

        self.assertEqual(graph.edges[1].from_node, 2)
        self.assertEqual(graph.edges[1].to_node, 3)
        self.assertEqual(graph.edges[1].from_start, False)
        self.assertEqual(graph.edges[1].to_end, True)

    def test_to_offset_based_graph(self):
        graph = Graph.from_file("simple_graph.json")
        obgraph = graph.get_offset_based_graph()

        self.assertEqual(obgraph,
                         GraphWithReversals({
                             1: Block(7),
                             2: Block(4),
                             3: Block(7)
                         },
                        {
                            1: [2],
                            2: [-3]
                        }))

class TestAlignment(unittest.TestCase):

    def setUp(self):
        self.alignment_json = '{"sequence": "TCCCCTTTTCCC", "identity": 0.75, "mapping_quality": 53, "path": {"name": "testread", "mapping": [{"rank": 1, "edit": [{"from_length": 5, "to_length": 5}], "position": {"offset": 2, "node_id": 1}}, {"rank": 2, "edit": [{"from_length": 4, "to_length": 4}, {"to_length": 3, "sequence": "CCC"}], "position": {"node_id": 2}}]}, "score": 9}'

    def test_alignment_from_json(self):
        alignment = Alignment.from_json(json.loads(self.alignment_json))
        self.assertEqual(alignment.identity, 0.75)
        path = alignment.path
        self.assertEqual(path.name, "testread")

if __name__ == "__main__":
    create_test_data()
    unittest.main()
