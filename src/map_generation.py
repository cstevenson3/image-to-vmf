import image_to_vmf
from image_processing import ColorHSV

class Map:
    def __init__(self):
        self.floors = []
        self.walls = []
        self.bombsites = []

class Floor:
    def __init__(self):
        self.border = []  # list of Vec
        self.bottom = 0.0
        self.top = 4.0

class Wall:
    def __init__(self):
        self.border = [] # list of Vec
        self.bottom = 0.0
        self.top = 50.0

class Bombsite:
    def __init__(self):
        self.border = [] # list of Vec
        self.bottom = 0.0
        self.top = 128.0

class Spawn:
    def __init__(self):
        self.border = [] # list of Vec
        self.bottom = 0.0
        self.top = 128.0
        self.team = "T" # T or CT

def generate_map(config, geometry):
    """ Take image geometry and generate a map """
    floors = []
    walls = []
    bombsites = []
    spawns = []
    for segment in geometry.segments.values():
        if segment.label.v == 0: # black segments
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["floor"], threshold=0.01):
            floor = Floor()
            floor.border = segment.border.vertices
            floor.top = 16
            floor.bottom = 0
            floors.append(floor)
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["wall"], threshold=0.01):
            wall = Wall()
            wall.border = segment.border.vertices
            wall.top = 192
            wall.bottom = 0
            walls.append(wall)
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["bombsite"], threshold=0.01):
            bombsite = Bombsite()
            bombsite.border = segment.border.vertices
            bombsite.top = 256
            bombsite.bottom = 0
            bombsites.append(bombsite)
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["t_spawn"], threshold=0.01):
            spawn = Spawn()
            spawn.border = segment.border.vertices
            spawn.top = 256
            spawn.bottom = 0
            spawn.team = "T"
            spawns.append(spawn)
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["ct_spawn"], threshold=0.01):
            spawn = Spawn()
            spawn.border = segment.border.vertices
            spawn.top = 256
            spawn.bottom = 0
            spawn.team = "CT"
            spawns.append(spawn)
            continue
    map = Map()
    map.floors = floors
    map.walls = walls
    map.bombsites = bombsites
    map.spawns = spawns
    return map
