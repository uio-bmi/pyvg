import unittest
from pyvg.sequences import SequenceRetriever
from offsetbasedgraph import Interval

class TestSequences(unittest.TestCase):

    def _test_from_vg_graph(self):
        retriever = SequenceRetriever.from_vg_graph("cactus-mhc.vg")

    def setUp(self):
        self.nodes = {
            1: "AAG",
            2: "GAA",
            3: "AGA"
        }
        self.retriever = SequenceRetriever(self.nodes)

    def test_single_node_interval(self):
        interval = Interval(0, 3, [1])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         self.nodes[1])

    def test_single_node_interval_with_offset(self):
        interval = Interval(1, 3, [1])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "AG")

    def test_single_node_interval_with_dual_offset(self):
        interval = Interval(1, 2, [1])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "A")

    def test_reversed_single_node_interval(self):
        interval = Interval(0, 3, [-1])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "GAA")

    def test_reversed_single_node_interval_with_dual_offsetl(self):
        interval = Interval(1, 2, [-3])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "G")

    def test_reversed_single_node_interval(self):
        interval = Interval(0, 3, [-1])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "GAA")

    def test_multiple_nodes_interval(self):
        interval = Interval(0, 3, [1, 2])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "AAGGAA")

    def test_multiple_nodes_interval_second_rp_reversed(self):
        interval = Interval(0, 3, [1, -2])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "AAGAAG")

    def test_long_interval(self):
        interval = Interval(1, 1, [1, 2, 3, -3, -2, -1])
        self.assertEqual(self.retriever.get_interval_sequence(interval),
                         "AGGAAAGAAGAAAGG")


if __name__ == "__main__":
    unittest.main()
