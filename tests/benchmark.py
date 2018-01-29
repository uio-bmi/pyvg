from pyvg.util import vg_json_file_to_interval_collection, vg_gam_file_to_interval_collection
import offsetbasedgraph as obg
from graph_peak_caller.extender import Extender
from graph_peak_caller.areas import ValuedAreas
from graph_peak_caller.densepileup import DensePileup

import logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s, %(levelname)s: %(message)s")


ob_graph = obg.GraphWithReversals.from_numpy_files("graph__")
graph = ob_graph
#intervals = vg_gam_file_to_interval_collection(None, "reads.gam", ob_graph)
intervals = None
def load_intervals():
    global intervals
    intervals = vg_json_file_to_interval_collection(None, "reads.json", ob_graph)

i = 0

def check_get_intervals_time():
    i = 0
    for interval in intervals:
        #print(interval)
        if i % 5000 == 0:
            logging.info("Interval %d" % i)

        i += 1



def run_extender():
    extender = Extender(ob_graph, 136)
    valued_areas = ValuedAreas(ob_graph)
    areas_list = (extender.extend_interval(interval)
                  for interval in intervals)

    i = 0
    touched_nodes = set()  # Speedup thing, keep track of nodes where areas are on
    for area in areas_list:
        if i % 5000 == 0:
            logging.info("Processing area %d" % i)
        i += 1

        valued_areas.add_binary_areas(area, touched_nodes)


def run_create_sample_pileup_new():
    extender = Extender(ob_graph, 136)
    valued_areas = ValuedAreas(graph)
    logging.info("Extending sample reads")
    areas_list = (extender.extend_interval(interval)
                  for interval in intervals)

    logging.info("Processing areas")

    pileup = DensePileup.create_from_binary_continous_areas(
                graph, areas_list)
    logging.info("Done")


def create_sample_pileup_with_graphindex(intervals):
    from graph_peak_caller.densepileupindex import GraphIndex
    from graph_peak_caller.sampleandcontrolcreator import create_sample_using_indexes
    graphindex = GraphIndex.create_from_graph(graph, 180)
    print("Graph index created")
    pileup = create_sample_using_indexes(intervals, graphindex, graph, 136)

load_intervals()
check_get_intervals_time()

"""
load_intervals()
run_extender()
load_intervals()
run_create_sample_pileup_new()
"""
