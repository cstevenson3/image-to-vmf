import vector
import map_generation

class VMF:
    def __init__(self):
        self._text = ""
    
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

class VMFObject:
    def __init__(self):
        pass

    @property
    def label(self):
        return "unlabelled"
    
    @property
    def properties(self):
        return {}
    
    @property
    def children(self):
        return []

    def isA(self, typ):
        return isinstance(self, typ)

    def write(self, vmf, indentation=0):
        vmf.text += ("    " * indentation) + "{0}\n".format(self.label)
        vmf.text += ("    " * indentation) + "{\n"
        for key in self.properties:
            value_str = ""
            value = self.properties[key]

            value_str = "{}".format(value)  # default

            if isinstance(value, (tuple, list)):
                value_str = "("
                for item in value:
                    value_str += "{0} ".format(item)
                value_str = value_str[:-1]
                value_str += ")"

            
            vmf.text += ("    " * (indentation + 1)) + "\"{0}\" \"{1}\"\n".format(key, value_str)
        for child in self.children:
            child.write(vmf, indentation + 1)
        vmf.text += ("    " * indentation) + "}\n\n"

class VMFBody(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._versioninfo = VersionInfo()
        self._visgroups = VisGroups()
        self._world = World()
        self._entities = []
        self._hiddens = []
        self._cameras = Cameras()
        self._cordon = Cordon()

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, value):
        self._world = value

    @property
    def children(self):
        return [self._versioninfo] +\
               [self._visgroups] +\
               [self._world] +\
               self._entities +\
               self._hiddens +\
               [self._cameras] +\
               [self._cordon]

    def write(self, vmf):
        for child in self.children:
            child.write(vmf, 0)

class VersionInfo(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
    
    @property
    def label(self):
        return "versioninfo"

    @property
    def properties(self):
        return {"editorversion":"400",
                "editorbuild": "3325",
                "mapversion": "0",
                "formatversion": "100",
                "prefab": "0"}

class VisGroups(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._visgroups = []
    
    @property
    def label(self):
        return "visgroups"

    @property
    def children(self):
        return self._visgroups

class World(VMFObject):
    id = 0
    def __init__(self):
        VMFObject.__init__(self)
        self._id = World.id
        World.id += 1
        self._solids = []
        self._hiddens = []
        self._groups = []
    
    @property
    def label(self):
        return "world"

    @property 
    def solids(self):
        return self._solids

    @solids.setter
    def solids(self, value):
        self._solids = value

    @property
    def properties(self):
        return {"id": self._id,
                "mapversion": 0,
                "classname": "worldspawn",
                "skyname": "sky_dust"}
    
    @property
    def children(self):
        return self._solids + self._hiddens + self._groups

class Cameras(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._cameras = []
    
    @property
    def label(self):
        return "cameras"
    
    @property
    def properties(self):
        return {"activecamera": -1}

    @property
    def children(self):
        return self._cameras

class Cordon(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
    
    @property
    def label(self):
        return "cordon"

    @property
    def properties(self):
        return {"mins": (99999, 99999, 99999),
                "maxs": (-99999, -99999, -99999),
                "active": 0}

class Brush(VMFObject):
    id = 0
    def __init__(self, sides):
        VMFObject.__init__(self)
        self._id = Brush.id
        Brush.id += 1
        self._sides = sides

    @property
    def label(self):
        return "solid"

    @property
    def properties(self):
        return {"id": self._id}

    @property
    def children(self):
        return self._sides

class Side(VMFObject):
    id = 0
    def __init__(self, plane):
        VMFObject.__init__(self)
        self._id = Side.id
        Side.id += 1
        self._plane = plane

    @property
    def label(self):
        return "side"

    @property
    def properties(self):
        return {"id": self._id,
                "plane": self._plane,
                "material": "BRICK/BRICKFLOOR001A",
                "uaxis": "[1 0 0 0] 0.25",
                "vaxis": "[0 0 -1 0] 0.25",
                "rotation": "0",
                "lightmapscale": "16",
                "smoothing_groups": "0"}

    @property
    def children(self):
        return []

def is_cc(a, b, c):
    val = vector.cross(vector.subtract(c, a), vector.subtract(b, a))
    if val == 0:
        return None
    return val > 0

def is_intersect(p1, p2, q1, q2):
    dir1 = is_cc(p1, p2, q1)
    dir2 = is_cc(p1, p2, q2)
    dir3 = is_cc(q1, q2, p1)
    dir4 = is_cc(q1, q2, p2)
    return dir1 != dir2 and dir3 != dir4

def can_connect(vertices, i1, i2):
    p1 = vertices[i1]
    p2 = vertices[i2]
    # check connecting line would start and end inside polygon
    if not is_cc(p1, vertices[(i1 + 1) % len(vertices)], p2):
        return False
    if not is_cc(p1, p2, vertices[(i1 - 1) % len(vertices)]):
        return False
    if not is_cc(p2, vertices[(i2 + 1) % len(vertices)], p1):
        return False
    if not is_cc(p2, p1, vertices[(i2 - 1) % len(vertices)]):
        return False

    # check connecting line would not cross another line segment
    for i in range(len(vertices)):
        if i == i1 or ((i + 1) % len(vertices)) == i1 or i == i2 or ((i + 1) % len(vertices)) == i2:
            # special case checked previously
            continue
        q1 = vertices[i]
        q2 = vertices[i % len(vertices)]
        if is_intersect(p1, p2, q1, q2):
            return False
        
    return True

def triangulate(vertices):
    if len(vertices) == 3:
        return [list(vertices)]
    
    triangles = []

    connected_vertices = [1]
    # starting from the first viable connection to index 1
    for index in range(3, len(vertices)):
        # if can connect from 1
        if can_connect(vertices, 1, index):
            connected_vertices.append(index)
    polygons = []
    current_streak = [1]
    for i in range(2, len(vertices) + 1):
        index = i % len(vertices)
        if index not in connected_vertices:
            current_streak.append(index)
            continue
        current_streak.append(index)
        polygons.append(current_streak[:])
        current_streak = [1, index]
    polygons.append(current_streak[:])
    
    for polygon in polygons:
        polygon_vertices = [vertices[i] for i in polygon]
        triangles += triangulate(polygon_vertices)
    return triangles

def add_z_dimension(triangles):
    for i in range(len(triangles)):
        for v in range(3):
            triangles[i][v] = (triangles[i][v][0], triangles[i][v][1], 0)

def build_object(segment):
    color_to_content = {}
    color_to_content[(0, 0, 0, 255)] = Floor
    color_to_content[(0, 255, 0, 255)] = Floor
    typ = color_to_content[segment.label]
    floor = typ(segment)
    return floor

def generate_floor_brushes(floor):
    brushes = []
    vertices = floor.border
    triangles = triangulate(vertices)
    add_z_dimension(triangles)
    # one brush per triangle
    for triangle in triangles:
        top_plane = [(0,floor.top,0), (1,floor.top,0), (0,floor.top,-1)]  # y=floor.top, arbitrary x,z
        bottom_plane = [(0,floor.bottom,0), (1,floor.bottom,0), (0,floor.bottom,-1)]  # y=floor.bottom, arbitrary x,z
        side_planes = []
        for i in range(3):
            side_plane = [triangle[i], vector.subtract(triangle[i], (0,0,1)), triangle[(i + 1) % 3]]
            side_planes.append(side_plane)
        planes = side_planes
        planes.append(top_plane)
        planes.append(bottom_plane)
        brush = Brush(planes)
        brushes.append(brush)
    return brushes

def generate_vmf(config, map):
    ''' Take a map and generate a valve map file object '''
    brushes = []
    for floor in map.floors:
        floor_brushes = generate_floor_brushes(floor)
        brushes += floor_brushes
    world = World()
    world.solids = brushes
    vmf_body = VMFBody()
    vmf_body.world = world
    return vmf_body
