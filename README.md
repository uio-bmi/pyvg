[![Build Status](https://travis-ci.org/uio-bmi/pyvg.svg?branch=master)](https://travis-ci.org/uio-bmi/pyvg)
[![codecov](https://codecov.io/gh/uio-bmi/pyvg/branch/master/graph/badge.svg)](https://codecov.io/gh/uio-bmi/pyvg)

# pyvg
pyvg is a lightweight Python package intended for making it easier to import and work with vg graphs and mapped reads in Python. It relies on vg graphs being converted to JSON, since importing proto-graphs is slow compared to JSON.

# Installation
pyvg requires Python3 and Pip in order to be installed.

```
git clone git@github.com:uio-bmi/pyvg.git
cd pyvg
pip3 install -e .
```

Alternatively use `pip install -e .` if your `pip` command installs Python 3 packages.

# Usage
## Graphs
Make sure your vg graph is in json-format. You can easily convert by doing:
```
vg view -jV graph.vg > graph.json
```

The graph can then be read into a Python Graph object by doing:
```
from pyvg import Graph
graph = Graph.from_file("graph.json")
# Convert to OffsetBasedGraph
obgraph = graph.get_offset_based_graph()
```

When working with huge graphs (millions of nodes), reading and converting will be faster if using the numpy backend of OffsetBasedGraphs, bypassing the Pyvg Graph object:
```
from pyvg.conversion import json_file_to_obg_numpy_graph
ob_graph = json_file_to_obg_numpy_graph("graph.json")

# Write ob graph to a compact numpy file:
ob_graph.to_numpy_file("graph.npy")
```

## Mappings
pyvg read vg mappings into an IntervalCollection. If you have a vg gam file, convert it to json first:
```
vg view -aj mappings.gam > mappings.json
```
Now, these can be read by pyvg:
```
from pyvg.conversion import vg_json_file_to_intervals
intervals = vg_json_file_to_intervals("mappings.json", ob_graph)

# Intervals is now a generator
for interval in intervals:
    print(interval)
```


# Development
pyvg only supports Python 3. Run tests from the root directory using py.test: `py.test`. Pull-requests are welcome!


