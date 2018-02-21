import unittest
from pyvg.conversion import vg_json_file_to_interval_collection, json_file_to_obg_numpy_graph
from testdata import create_test_data, simple_graph

class TestReadConversion(unittest.TestCase):

    def setUp(self):
        reads =  '{"sequence": "CCTTTTCCC", "identity": 0.75, "mapping_quality": 53, "path": {"name": "testread", "mapping": [{"rank": 1, "edit": [{"from_length": 5, "to_length": 5}], "position": {"offset": 2, "node_id": 1}}, {"rank": 2, "edit": [{"from_length": 4, "to_length": 4}, {"to_length": 3, "sequence": "CCC"}], "position": {"node_id": 2}}]}, "score": 9}'
        reads += "\n"
        reads += '{"sequence": "CCTTTTCCC", "identity": 0.8, "mapping_quality": 60, "path": {"name": "testread", "mapping": [{"rank": 1, "edit": [{"from_length": 5, "to_length": 5}], "position": {"offset": 2, "node_id": 1}}, {"rank": 2, "edit": [{"from_length": 4, "to_length": 4}, {"to_length": 3, "sequence": "CCC"}], "position": {"node_id": 2}}]}, "score": 9}'

        f = open("alignments.json", "w")
        f.write(reads)
        f.close()
        self.graph = simple_graph

    def test_json_reads_to_intervalcollection(self):
        intervals = vg_json_file_to_interval_collection("alignments.json", self.graph)
        intervals = intervals.intervals

        for interval in intervals:
            assert interval.length() == 9


class TestGraphConversion(unittest.TestCase):

    def test_simple(self):
        graph = json_file_to_obg_numpy_graph("tests/simple_graph.json")
        assert graph == simple_graph


if __name__ == "__main__":
    create_test_data()
    unittest.main()