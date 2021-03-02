import vector
from vector import *

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

    def set_material(self, material):
        ''' material is a string e.g. "BRICK/BRICK_FLOOR_02" '''
        for side in self._sides:
            side._material = material

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
        self._material = "BRICK/BRICK_FLOOR_02"

    @property
    def label(self):
        return "side"

    @property
    def properties(self):
        return {"id": self._id,
                "plane": self._plane,
                "material": self._material,
                "uaxis": self._uaxis,
                "vaxis": self._vaxis,
                "rotation": "0",
                "lightmapscale": "16",
                "smoothing_groups": "0"}

    @property
    def children(self):
        return []

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

class Buyzone(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._id = VMFObject.id
        VMFObject.id += 1
        self._editor = Editor()
        self._editor._color = (220, 30, 220)
        self._solids = []
        self._team_num = 2  # 2 for T, 3 for CT

    @property
    def label(self):
        return "entity"

    @property
    def properties(self):
        return {"id": self._id,
                "classname": "func_buyzone",
                "TeamNum": self._team_num}

    @property
    def children(self):
        return self._solids + [Editor()]

class Spawn(VMFObject):
    def __init__(self):
        VMFObject.__init__(self)
        self._id = VMFObject.id
        VMFObject.id += 1
        self._editor = Editor()
        self._editor._color = (220, 30, 220)
        self._classname = "info_player_terrorist"
        self._origin = (0, 0, 0)

    @property
    def label(self):
        return "entity"

    @property
    def properties(self):
        return {"id": self._id,
                "classname": self._classname,
                "angles": (0, 0, 0),
                "enabled": 1,
                "origin": self._origin}

    @property
    def children(self):
        return [Editor()]