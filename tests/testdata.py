from offsetbasedgraph import GraphWithReversals, Block

def create_test_data():
    simple_graph = """
    {
    "node": [
        {"id": 1, "sequence": "TTTCCCC"},
        {"id": 2, "sequence": "TTTT"},
        {"id": 3, "sequence": "CCCCTTT"}
    ],
    "edge": [
        {"from": 1, "to": 2},
        {"from": 2, "to": 3, "to_end": true}
    ]
    }
    """

    f = open("simple_graph.json", "w")
    f.write(simple_graph.replace("\n", " "))
    f.close()

simple_graph = GraphWithReversals({
                             1: Block(7),
                             2: Block(4),
                             3: Block(7)
                         },
                        {
                            1: [2],
                            2: [-3]
                        })
