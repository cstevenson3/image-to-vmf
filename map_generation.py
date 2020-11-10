import image_to_vmf

class Map:
    def __init__(self):
        self._floors = []
        self._walls = []

    @property
    def floors(self):
        return self._floors

    @floors.setter
    def floors(self, value):
        self._floors = value

    @property
    def walls(self):
        return self._walls

class Floor:
    def __init__(self):
        self._border = []  # list of Vec
        self._bottom = 0.0
        self._top = 4.0

    @property
    def border(self):
        return self._border

    @border.setter
    def border(self, value):
        self._border = value

    @property
    def bottom(self):
        return self._bottom
    
    @bottom.setter
    def bottom(self, value):
        self._bottom = value

    @property
    def top(self):
        return self._top
    
    @top.setter
    def top(self, value):
        self._top = value
    

class Wall:
    def __init__(self):
        self._border = [] # list of Vec
        self._bottom = 0.0
        self._top = 50.0

def generate_map(config, geometry):
    """ Take image geometry and generate a map """
    floors = []
    for segment in geometry.segments.values():
        floor = Floor()
        floor.border = segment.border
        floor.top = 16
        floor.bottom = 0
    map = Map()
    map.floors = floors
    return map
