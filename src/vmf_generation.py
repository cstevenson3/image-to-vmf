import vector
from vector import *
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

def vmf_value_format(value, outer=True):
    value_str = "{}".format(value)  # default
    if isinstance(value, (tuple, list)):
        opener = "[" if isinstance(value, list) else "("
        closer = "]" if isinstance(value, list) else ")"
        if not outer:
            value_str = opener
        else:
            value_str = ""
        for item in value:
            value_str += "{0} ".format(vmf_value_format(item, outer=False))
        value_str = value_str[:-1]
        if not outer:
            value_str += closer
    return value_str

class VMFObject:
    id = 1
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
            value = self.properties[key]
            value_str = vmf_value_format(value)
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
                "editorbuild": "8456",
                "mapversion": "1",
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

class ViewSettings(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
    
    @property
    def label(self):
        return "viewsettings"
    
    @property
    def properties(self):
        return {"bSnapToGrid": 1,
                "bShowGrid": 1,
                "bShowLogicalGrid": 0,
                "nGridSpacing": 64,
                "bShow3DGrid": 0}

    @property
    def children(self):
        return []

class World(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._id = VMFObject.id
        VMFObject.id += 1
        self.solids = []
        self._hiddens = []
        self._groups = []
    
    @property
    def label(self):
        return "world"

    @property
    def properties(self):
        return {"id": self._id,
                "mapversion": 0,
                "classname": "worldspawn",
                "skyname": "sky_dust"}
    
    @property
    def children(self):
        return self.solids + self._hiddens + self._groups

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
        # "mins": (99999, 99999, 99999),
        # "maxs": (-99999, -99999, -99999),
        return {"active": 0}

class Brush(VMFObject):
    def __init__(self, sides):
        VMFObject.__init__(self)
        self._id = VMFObject.id
        VMFObject.id += 1
        self._sides = sides

    @property
    def label(self):
        return "solid"

    @property
    def properties(self):
        return {"id": self._id}

    @property
    def children(self):
        return self._sides + [Editor()]

class Editor(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._color = (0, 243, 144)

    @property
    def label(self):
        return "editor"

    @property
    def properties(self):
        return {"color": self._color,
                "visgroupshown": 1,
                "visgroupautoshown": 1}

    @property
    def children(self):
        return []

class Bombsite(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._id = VMFObject.id
        VMFObject.id += 1
        self._editor = Editor()
        self._editor._color = (220, 30, 220)
        self._solids = []

    @property
    def label(self):
        return "entity"

    @property
    def properties(self):
        return {"id": self._id,
                "classname": "func_bomb_target",
                "heistbomb": 0}

    @property
    def children(self):
        return self._solids + [Editor()]

def generate_uv_axes(plane):
    u = vector.subtract(plane[1], plane[0])
    v = vector.subtract(plane[2], plane[0])
    absent = [(0 if u[i] == 0 and v[i] == 0 else 1) for i in range(3)]
    absent_axis = sum([i for i in range(3) if absent[i] == 0])
    available_axes = [0, 1, 2]
    available_axes.remove(absent_axis)

    u = [0 for i in range(3)]
    u[available_axes[0]] = 1

    v = [0 for i in range(3)]
    v[available_axes[1]] = 1

    u = list(u)
    u.append(0)
    v = list(v)
    v.append(0)

    uaxis = (u, 0.25)
    vaxis = (v, 0.25)
    return (uaxis, vaxis)

class Side(VMFObject):
    id = 1
    def __init__(self, plane):
        VMFObject.__init__(self)
        self._id = Side.id
        Side.id += 1
        self._plane = plane
        self._uaxis, self._vaxis = generate_uv_axes(plane)

    @property
    def label(self):
        return "side"

    @property
    def properties(self):
        return {"id": self._id,
                "plane": self._plane,
                "material": "BRICK/BRICK_FLOOR_02",
                "uaxis": self._uaxis,
                "vaxis": self._vaxis,
                "rotation": "0",
                "lightmapscale": "16",
                "smoothing_groups": "0"}

    @property
    def children(self):
        return []


def triangulate(vertices, next_indices=None):
    ''' Triangulate a counter-clockwise polygon 
    into counter-clockwise triangles. Returns indices '''
    # trick to avoid messing up the default arg
    indices = None
    if next_indices is None:
        indices = [i for i in range(len(vertices))]
    else:
        indices = next_indices[:]

    if len(indices) == 3:
        return [list(indices)]
    
    chosen_triangle = None
    # for each potential triangle start index
    for i in range(len(indices)):
        index_0 = indices[i]
        index_1 = indices[(i + 1) % len(indices)]
        index_2 = indices[(i + 2) % len(indices)]
        triangle = [vertices[index_0], vertices[index_1], vertices[index_2]]
        if is_cc(*triangle):
            line_0 = (triangle[0], triangle[1])
            line_1 = (triangle[1], triangle[2])
            line_2 = (triangle[2], triangle[0])
            no_self_intersection = True
            for j in range(len(indices)):
                j_0 = indices[j]
                j_1 = indices[(j + 1) % len(indices)]
                other_line = (vertices[j_0], vertices[j_1])
                line_0_intersect = segments_intersect(line_0, other_line)
                line_1_intersect = segments_intersect(line_1, other_line)
                line_2_intersect = segments_intersect(line_2, other_line)
                if line_0_intersect or line_1_intersect or line_2_intersect:
                    no_self_intersection = False
                    break
            for point in vertices:
                if point_in_triangle(point, triangle):
                    no_self_intersection = False
                    break
            if no_self_intersection:
                chosen_triangle = triangle
                next_indices = indices[:]
                next_indices.pop((i + 1) % len(indices))
                other_triangles = triangulate(vertices, next_indices)
                return [[index_0, index_1, index_2]] + other_triangles

    raise AssertionError("Polygon should be CCW")

def add_z_dimension(triangles):
    for i in range(len(triangles)):
        for v in range(3):
            triangles[i][v] = (triangles[i][v][0], triangles[i][v][1], 0)

def generate_floor_brushes(floor):
    brushes = []
    vertices = floor.border
    triangle_indices = triangulate(vertices)
    triangles = [[vertices[i], vertices[j], vertices[k]] for i,j,k in triangle_indices]
    # make sure all are cc
    for i in range(len(triangles)):
        if not is_cc(*(triangles[i])):
            triangles[i].reverse()
    add_z_dimension(triangles)
    # one brush per triangle
    for triangle in triangles:
        top_plane = [(triangle[i][0],triangle[i][1],floor.top) for i in range(3)]
        top_plane.reverse()  # make it clockwise from the top
        bottom_plane = [(triangle[i][0],triangle[i][1],floor.bottom) for i in range(3)]
        side_planes = []
        for i in range(3):
            vertex_1 = triangle[i]
            vertex_2 = triangle[(i - 1) % 3]
            side_plane = [(vertex_1[0],vertex_1[1],floor.top), (vertex_1[0],vertex_1[1],floor.bottom), (vertex_2[0],vertex_2[1],floor.top)]
            side_planes.append(side_plane)
        planes = side_planes
        planes.append(top_plane)
        planes.append(bottom_plane)
        sides = [Side(plane) for plane in planes]
        brush = Brush(sides)
        brushes.append(brush)
    return brushes

def generate_vmf_body(config, map):
    ''' Take a map and generate a valve map file object '''
    brushes = []
    entities = []
    for floor in map.floors:
        floor_brushes = generate_floor_brushes(floor)
        brushes += floor_brushes
    for wall in map.walls:
        wall_brushes = generate_floor_brushes(wall)  # same method should work for walls
        brushes += wall_brushes
    for bombsite in map.bombsites:
        bombsite_brushes = generate_floor_brushes(bombsite)
        bomb = Bombsite()
        for brush in bombsite_brushes:
            bomb._solids.append(brush)
        entities.append(bomb)

    world = World()
    world.solids = brushes
    vmf_body = VMFBody()
    vmf_body.world = world
    vmf_body._entities = entities
    return vmf_body
