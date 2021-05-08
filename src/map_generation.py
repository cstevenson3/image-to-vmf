import image_to_vmf
from image_processing import ColorHSV

class Map:
    def __init__(self):
        self.floors = []
        self.walls = []
        self.bombsites = []
        self.buyzones = []
        self.spawns = []

    def scale(self, factor):
        for bobj in self.floors + self.walls + self.bombsites + self.buyzones:
            bobj.scale(factor)
        for spawn in self.spawns:
            spawn.scale(factor)

class BorderedObject:
    def __init__(self):
        self.border = []

    def scale(self, factor):
        self.border = self.border[:]  # some objects share a border before this clone
        for i in range(len(self.border)):
            temp = self.border[i]
            self.border[i] = (temp[0] * factor, temp[1] * factor)


class Floor(BorderedObject):
    def __init__(self):
        self.bottom = 0.0
        self.top = 4.0
        self.material = None

class Wall(BorderedObject):
    def __init__(self):
        self.bottom = 0.0
        self.top = 50.0
        self.material = None

class Bombsite(BorderedObject):
    def __init__(self):
        self.bottom = 0.0
        self.top = 128.0

class Buyzone(BorderedObject):
    def __init__(self):
        self.bottom = 0.0
        self.top = 128.0
        self.team = "T" # T or CT

class Spawn:
    def __init__(self):
        self.origin = (0, 0, 0)
        self.team = "T" # T or CT
    
    def scale(self, factor):
        temp = self.origin
        self.origin = (temp[0] * factor, temp[1] * factor, temp[2])

def generate_map(config, geometry):
    """ Take image geometry and generate a map """
    floors = []
    walls = []
    bombsites = []
    buyzones = []
    spawns = []
    for segment in geometry.segments.values():
        if segment.label.v == 0: # black segments
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["floor"], threshold=0.01):
            floor = Floor()
            floor.border = segment.border.vertices
            floor.top = 0
            floor.bottom = -16
            floors.append(floor)
            floor.material = "DEV/DEV_MEASUREGENERIC01B"
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["wall"], threshold=0.01):
            wall = Wall()
            wall.border = segment.border.vertices
            wall.top = 192
            wall.bottom = 0
            wall.material = "DEV/DEV_MEASUREGENERIC01"
            walls.append(wall)
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["bombsite"], threshold=0.01):
            bombsite = Bombsite()
            bombsite.border = segment.border.vertices
            bombsite.top = 256
            bombsite.bottom = 0
            bombsites.append(bombsite)

            floor = Floor()
            floor.border = segment.border.vertices
            floor.top = 0
            floor.bottom = -16
            floor.material = "PROPS/HAZARDSTRIP001A"
            floors.append(floor)
            continue
        if ColorHSV.almost_equal(segment.label, config.color_mappings["t_buyzone"], threshold=0.01) \
        or ColorHSV.almost_equal(segment.label, config.color_mappings["ct_buyzone"], threshold=0.01):
            buyzone = Buyzone()
            buyzone.border = segment.border.vertices
            buyzone.top = 256
            buyzone.bottom = 0
            buyzone.team = "T" if ColorHSV.almost_equal(segment.label, config.color_mappings["t_buyzone"], threshold=0.01) else "CT"
            buyzones.append(buyzone)

            floor = Floor()
            floor.border = segment.border.vertices
            floor.top = 0
            floor.bottom = -16
            floors.append(floor)

            vertices = segment.border.vertices
            sum_of_vertices = [sum([vertices[i][j] for i in range(len(vertices))]) for j in range(2)]
            average_vertex = [sum_of_vertices[i] / len(vertices) for i in range(2)]

            spawn_offset = 50  # space out spawns this much
            spawn_vertices = [[(average_vertex[0] + x_mult * spawn_offset, average_vertex[1] + y_mult * spawn_offset) for x_mult in [-1, 0, 1]] for y_mult in [-1, 0, 1]]
            
            for row in spawn_vertices:
                for vertex in row:
                    spawn = Spawn()
                    spawn.origin = (vertex[0], vertex[1], 2) # just above ground
                    spawn.team = "T" if ColorHSV.almost_equal(segment.label, config.color_mappings["t_buyzone"], threshold=0.01) else "CT"
                    spawns.append(spawn)
            continue
    map = Map()
    map.floors = floors
    map.walls = walls
    map.bombsites = bombsites
    map.buyzones = buyzones
    map.spawns = spawns
    return map
