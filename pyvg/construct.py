from .util import call_vg
import logging

def construct_graph_from_msa(msa_file, out_file_name):
    call_vg("vg construct -M %s -F fasta" % (msa_file), False, out_file_name + ".tmp")
    call_vg("vg mod -c %s" % out_file_name + ".tmp", False, out_file_name + "-2.tmp")
    call_vg("vg mod -s %s" % out_file_name + "-2.tmp", False, out_file_name)
    logging.info("Done constructing graph, wrote to %s" % out_file_name)