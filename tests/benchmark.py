from pyvg.util import vg_json_file_to_interval_collection, vg_gam_file_to_interval_collection
import offsetbasedgraph as obg
from graph_peak_caller.extender import Extender
from graph_peak_caller.areas import ValuedAreas


ob_graph = obg.GraphWithReversals.from_numpy_files("graph__")
#intervals = vg_gam_file_to_interval_collection(None, "reads.gam", ob_graph)
intervals = vg_json_file_to_interval_collection(None, "reads.json", ob_graph)

i = 0

def check_get_intervals_time():
    for interval in intervals:
        #print(interval)
        if i % 5000 == 0:
            print("Interval %d" % i)

        i += 1



def run_extender():
    extender = Extender(ob_graph, 140)
    valued_areas = ValuedAreas(ob_graph)
    areas_list = (extender.extend_interval(interval)
                  for interval in intervals)

    i = 0
    touched_nodes = set()  # Speedup thing, keep track of nodes where areas are on
    for area in areas_list:
        if i % 5000 == 0:
            print("Processing area %d" % i)
        i += 1

        valued_areas.add_binary_areas(area, touched_nodes)


run_extender()