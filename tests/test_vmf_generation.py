from src.image_to_vmf import *
from src.map_generation import *
from src.vmf_generation import *

def test_triangulate():
    triangles = triangulate([(0,3), (1,2), (0,0), (2,0), (1,1), (3,2)])
    reference = [[2,3,4], [1,2,4], [1,4,5], [0,1,5]]
    assert(all([triangles[i] == reference[i] for i in range(len(reference))]))

def test_generate_vmf():
    floor = Floor()
    floor.border = [(0,0), (1,0), (1,1), (0,1)]
    floor.bottom = 0
    floor.top = 16
    map = Map()
    map.floors.append(floor)
    vmf_body = generate_vmf_body(import_config("tests/test_data/config.json"), map)
    vmf = VMF()
    vmf_body.write(vmf)
    output = open("tests/test_data/output.vmf", "w")
    output.write(vmf.text)
    output.close()
