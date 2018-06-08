import logging
from .util import call_vg


def graph_to_json(graph_file_name, json_file_name):
    call_vg("vg view -Vj %s" % graph_file_name, out_file=json_file_name)
    logging.info("Done converting to json. Wrote to %s" % json_file_name)

