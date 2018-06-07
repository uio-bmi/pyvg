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

