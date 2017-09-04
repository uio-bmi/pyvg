from pyvg import util, vg
import offsetbasedgraph


def test_json_reader_equals_gam_reader():
    vg_graph = None
    #vg_graph = vg.Graph.create_from_file("x.json", False, "chr4")

    obg_graph = offsetbasedgraph.Graph.from_file("x.offsetbasedgraph")
    obg_intervals1 = []
    for interval in util.vg_gam_file_to_intervals(vg_graph, "test.gam", obg_graph):
        print(interval)
        obg_intervals1.append(interval)

    obg_intervals2 = []
    for interval in util.vg_mapping_file_to_interval_list(vg_graph, "test.json", obg_graph):
        obg_intervals2.append(interval)

    assert len(obg_intervals1) == len(obg_intervals2)

    for i in range(0, len(obg_intervals1)):
        assert obg_intervals1[i] == obg_intervals2[i]


test_json_reader_equals_gam_reader()