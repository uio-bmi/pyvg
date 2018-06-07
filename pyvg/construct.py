from .util import call_vg
import logging

def construct_graph_from_msa(msa_file, out_file_name):
    call_vg("vg construct -M %s -F fasta > %s" % (msa_file, out_file_name + ".tmp"))
    call_vg("vg mod -c %s > %s" % (out_file_name + ".tmp", out_file_name + "-2.tmp"))
    call_vg("vg mod -s %s > %s" % (out_file_name + "-2.tmp", out_file_name))
    logging.info("Done constructing graph, wrote to %")