import re
import io
from itertools import islice, chain
from .util import call_vg
from Bio.SeqIO.FastaIO import SimpleFastaParser
from subprocess import Popen, PIPE, check_output
import logging


def fasta_parser(file_name):
    with open(file_name) as f:
        for title, sequence in SimpleFastaParser(f):
            yield title, sequence


def align_safe(sequence_id, sequence, vg_graph_file_name):
    command = "vg align -Q %s -s %s %s" % (sequence_id, sequence,
                                           vg_graph_file_name)
    align_process = Popen(command.split(), stdout=PIPE)
    command = "vg view -aj -"
    view_process = Popen(command.split(), stdin=align_process.stdout,
                         stdout=PIPE)
    return io.TextIOWrapper(view_process.stdout)


def align_sequence(sequence_id, sequence, vg_graph_file_name):
    vg_alignment = call_vg("vg align -Q %s -s %s %s" % (sequence_id, sequence, vg_graph_file_name),
                            return_raw=True)
    with open("tmp.vg", "wb") as tmp_file:
        tmp_file.write(vg_alignment)

    json_alignment = call_vg("vg view -aj 80tmp.vg")
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


def _chunks(iterator, N):
    for first in iterator:
        yield chain([first], islice(iterator, N-1))


def align_fasta_to_graph_paralell(fasta_file_name, graph_file_name, out_file_name):
    output_file = open(out_file_name, "w")

    def assert_name(name, json_alignment):
        try:
            found_name = re.search(r"\"name\": ?\"([A-Z0-9_\-\.a-z]+)+\"",
                               json_alignment, re.IGNORECASE).group(1)
        except AttributeError as e:
            print("Search for name gave no results for %s" % json_alignment)
            raise
        assert found_name == name or found_name == name.split()[0], (name, found_name)
        return json_alignment

    output_file = open(out_file_name, "w")
    for chunk in _chunks(fasta_parser(fasta_file_name), 100):
        pipes = {title: align_safe(title.split()[0], sequence, graph_file_name)
                 for title, sequence in chunk}
        alignments = (assert_name(title, str(pipe.read()))
                      for title, pipe in pipes.items())
        output_file.writelines(alignments)
    output_file.close()

    logging.info("Wrote to %s" % out_file_name)
