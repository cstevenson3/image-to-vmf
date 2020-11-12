import image_to_vmf

class Map:
    def __init__(self):
        self.floors = []
        self.walls = []

class Floor:
    def __init__(self):
        self.border = []  # list of Vec
        self.bottom = 0.0
        self.top = 4.0

class Wall:
    def __init__(self):
        self._border = [] # list of Vec
        self._bottom = 0.0
        self._top = 50.0

def generate_map(config, geometry):
    """ Take image geometry and generate a map """
    floors = []
    for segment in geometry.segments.values():
        if segment.label.v == 0:
            continue
        floor = Floor()
        floor.border = segment.border.vertices
        floor.top = 16
        floor.bottom = 0
        floors.append(floor)
    map = Map()
    map.floors = floors
    return map
