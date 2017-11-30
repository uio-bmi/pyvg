import subprocess
import logging

def map(fastq_file_name, xg_index_file_name,
        gcsa_index_file_name, out_gam_file_name):

    command = "~/bin/vg map -D -g %s -x %s -K -Z 1 -f %s > %s" % (gcsa_index_file_name,
                                                    xg_index_file_name,
                                                    fastq_file_name,
                                                    out_gam_file_name)
    print(command)
    subprocess.check_output(command, shell=True)


if __name__ == "__main__":
    map("test.fastq",
        "haplo1kg50-mhc.xg",
        "haplo1kg50-mhc.gcsa",
        "out.gam")

