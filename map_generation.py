import image_to_vmf

class Map:
    def __init__(self):
        self._floors = []
        self._walls = []

    @property
    def floors(self):
        return self._floors

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

    @property
    def bottom(self):
        return self._bottom

    @property
    def top(self):
        return self._top
    

class Wall:
    def __init__(self):
        self._border = [] # list of Vec
        self._bottom = 0.0
        self._top = 50.0

def generate_map(config, geometry):
    """ Take image geometry and generate a map """
    assert isinstance(config, image_to_vmf.Config)
    assert isinstance(config, image_processing.Geometry)
    
