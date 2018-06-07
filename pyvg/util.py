import os
import subprocess
import logging

def call_vg(command, return_raw=False):
    logging.debug("Running vg command: " + command)
    res = subprocess.check_output(command.split())
    if res == "" or return_raw:
        return res
    return res.decode("utf-8")

