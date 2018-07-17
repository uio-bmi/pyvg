import os
import subprocess
import logging

def call_vg(command, return_raw=False, out_file=None):
    logging.debug("Running vg command: " + command)

    if out_file is not None:
        with open(out_file, "w") as outfile:
            subprocess.call(command.split(), stdout=outfile)

        logging.info("Wrote to %s" % out_file)
        return
    res = subprocess.check_output(command.split())
    if res == "" or return_raw:
        return res
    return res.decode("utf-8")


def get_stats(graph_file_name):

    stats = call_vg("vg stats -lz %s" % graph_file_name)
    lines = stats.split("\n")
    return {
        "nodes": lines[0].split()[1],
        "edges": lines[1].split()[1],
        "length": lines[2].split()[1],
    }

