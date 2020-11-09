import image_to_vmf

class Map:
    def __init__(self):
        self._floors = []
        self._walls = []

class Floor:
    def __init__(self):
        self._boundary = []
        self._bottom = 0.0
        self._top = 4.0

class Wall:
    def __init__(self):
        self._boundary = []
        self._bottom = 0.0
        self._top = 50.0

def generate_map(config, geometry):
    """ Take image geometry and generate a map """
    assert isinstance(config, image_to_vmf.Config)
    assert isinstance(config, image_processing.Geometry)
