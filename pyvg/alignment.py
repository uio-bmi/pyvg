import re
from .util import call_vg
from Bio.SeqIO.FastaIO import SimpleFastaParser
from subprocess import Popen, PIPE
import logging


def fasta_parser(file_name):
    with open(file_name) as f:
        for title, sequence in SimpleFastaParser(f):
            yield title, sequence

def align_safe(sequence_id, sequence, vg_graph_file_name):
    command = "vg align -Q %s -s %s %s" % (sequence_id, sequence, vg_graph_file_name)
    align_process = Popen(command.split(), stdout=PIPE, stdin=PIPE)
    command = "vg view -aj -"
    view_process = Popen(command.split(), stdin=align_process.stdout, stdout=PIPE)
    return view_process.stdout

def align_sequence(sequence_id, sequence, vg_graph_file_name):
    vg_alignment = call_vg("vg align -Q %s -s %s %s" % (sequence_id, sequence, vg_graph_file_name),
                            return_raw=True)
    with open("tmp.vg", "wb") as tmp_file:
        tmp_file.write(vg_alignment)

    json_alignment = call_vg("vg view -aj tmp.vg")
    return json_alignment

def align_fasta_to_graph(fasta_file_name, graph_file_name, out_file_name):
    output_file = open(out_file_name, "w")
    for title, sequence in fasta_parser(fasta_file_name):
        print("Aligning %s" % title)
        json_alignment = align_sequence("%s" % title.split()[0], sequence, graph_file_name)
        name_search = re.search(r"\"name\":\"([A-Z0-9_\-\.a-z]+)+\"", json_alignment, re.IGNORECASE)
        if name_search:
            name = name_search.group(1)
        else:
            raise Exception("Did not found name")
        
        print("  Matched %s" % name)
        output_file.writelines([json_alignment])
    output_file.close()
    logging.info("Wrote to %s" % out_file_name)

def align_fasta_to_graph_paralell(fasta_file_name, graph_file_name, out_file_name):
    output_file = open(out_file_name, "w")
    name_search = lambda x: re.search(r"\"name\":\"([A-Z0-9_\-\.a-z]+)+\"", x, re.IGNORECASE)
    alignment_pipes = {title: align_safe(title.split()[0], sequence, graph_file_name)
                       for title, name in fasta_parser(fasta_file_name)}
    names = {title: pipe.read() for title, pipe in alignment_pipes()}

    for title, sequence in fasta_parser(fasta_file_name):
        print("Aligning %s" % title)
        json_alignment = align_sequence("%s" % title.split()[0], sequence, graph_file_name)
        name_search = re.search(r"\"name\":\"([A-Z0-9_\-\.a-z]+)+\"", json_alignment, re.IGNORECASE)
        if name_search:
            name = name_search.group(1)
        else:
            raise Exception("Did not found name")
        
        print("  Matched %s" % name)
        output_file.writelines([json_alignment])
    output_file.close()
    logging.info("Wrote to %s" % out_file_name)
