import vector
from vector import *
import map_generation
import constructs
from vmf_objects import *


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
        if floor.material != None:
            [brush.set_material(floor.material) for brush in floor_brushes]
        brushes += floor_brushes
    for wall in map.walls:
        wall_brushes = generate_floor_brushes(wall)  # same method should work for walls
        if wall.material != None:
            [brush.set_material(wall.material) for brush in wall_brushes]
        brushes += wall_brushes
    for bombsite in map.bombsites:
        bombsite_brushes = generate_floor_brushes(bombsite)
        bomb = Bombsite()
        for brush in bombsite_brushes:
            brush.set_material("TOOLS/TOOLSNODRAW")
            bomb._solids.append(brush)
        entities.append(bomb)
    for buyzone in map.buyzones:
        buyzone_brushes = generate_floor_brushes(buyzone)
        buyz = Buyzone()
        buyz._team_num = 2 if buyzone.team == "T" else 3  # 2 for T, 3 for CT
        for brush in buyzone_brushes:
            brush.set_material("TOOLS/TOOLSNODRAW")
            buyz._solids.append(brush)
        entities.append(buyz)
    for spawn in map.spawns:
        spaw = Spawn()
        spaw._origin = spawn.origin
        spaw._classname = "info_player_terrorist" if spawn.team == "T" else "info_player_counterterrorist"
        entities.append(spaw)
    # skybox
    skybox_brushes = constructs.hollow_box(-128, 512, -128, 512, -32, 512)
    [brush.set_material("TOOLS/TOOLSSKYBOX") for brush in skybox_brushes]
    brushes += skybox_brushes
    world = World()
    world.solids = brushes
    vmf_body = VMFBody()
    vmf_body.world = world
    vmf_body._entities = entities
    return vmf_body
