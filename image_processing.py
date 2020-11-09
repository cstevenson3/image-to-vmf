import png
import sys

import operator
import vector

class Geometry:
    def __init__(self):
        self._segments = {}  # key id, value ImageSegment
        self._neighbours = {} # key id, value list of ids of neighbour ImageSegment's

class Pixel:
    def __init__(self, r, g, b, a):
        self._r = r
        self._g = g
        self._b = b
        self._a = a
        self._segmented = None
    
    @property
    def r(self):
        return self._r

    @property
    def g(self):
        return self._g

    @property
    def b(self):
        return self._b

    @property 
    def a(self):
        return self._a

    @property
    def color(self):
        return (self._r, self._g, self._b, self._a)

    def discovered(self):
        return self._segmented is not None

    def set_discovered(self):
        self._segmented = False

    def set_segmented(self):
        self._segmented = True

    def segmented(self):
        return self._segmented is True

    def __repr__(self):
        return "Pixel({0:<3},{1:<3},{2:<3},{3:<3})".format(self._r, self._g, self._b, self._a)

class PixelRow:
    def __init__(self, width):
        self._width = width
        self._pixels = [None for i in range(width)]

    def __getitem__(self, key):
        return self._pixels[key]

    def __setitem__(self, key, value):
        self._pixels[key] = value

    def __len__(self):
        return self._width

    def __iter__(self):
        return self._pixels.__iter__()

    def __str__(self):
        result = ""
        for pixel in self._pixels:
            result += repr(pixel) + " | "
        return result

class Image:
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._rows = [PixelRow(width) for i in range(height)]

    @property
    def rows():
        return self._rows

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def __getitem__(self, key):
        return self._rows[key]

    def __len__(self):
        return self._height

    def __str__(self):
        result = ""
        for pixel_row in self._rows:
            result += str(pixel_row) + "\n"
        return result

    def __iter__(self):
        return self._rows.__iter__()

class Border:
    def __init__(self, vertices):
        self._vertices = vertices

    def add_vertex(self, vertex):
        self._vertices.append(vertex)
    
    def remove(self, vertex_index):
        self._vertices.pop(vertex_index)

    def area_change_on_removing(self, vertex_index):
        previous_vertex = self._vertices[(vertex_index - 1) % len(self._vertices)]
        vertex = self._vertices[vertex_index % len(self._vertices)]
        next_vertex = self._vertices[(vertex_index + 1) % len(self._vertices)]
        area_change = abs(vector.cross(vector.subtract(previous_vertex, vertex), vector.subtract(next_vertex, vertex))) / float(2)
        return area_change

    def refine(self, tolerance):
        proposed_removal_vertex_index = None
        proposed_area_change = 0
        while(proposed_area_change < tolerance):
            # make change
            if proposed_removal_vertex_index is not None:
                self.remove(proposed_removal_vertex_index)
            # propose a new removal
            best_removal_vertex_index = None
            best_area_change = float("inf")
            for index in range(len(self._vertices)):
                area_change = self.area_change_on_removing(index)
                if area_change < best_area_change:
                    best_removal_vertex_index = index
                    best_area_change = area_change
            proposed_removal_vertex_index = best_removal_vertex_index
            proposed_area_change = best_area_change

    @property
    def vertices(self):
        return self._vertices

    def __str__(self):
        return str(self._vertices)

def turn_left(direction):
    return (direction[1], -direction[0])

def turn_right(direction):
    return (-direction[1], direction[0])

def direction_to_corner(direction):
    if direction == (0, 1):
        return (0, 1)
    if direction == (1, 0):
        return (1, 1)
    if direction == (0, -1):
        return (1, 0)
    if direction == (-1, 0):
        return (0, 0)

class ImageSegment:
    # pixels is (x,y) points
    id = 0
    def __init__(self, label, pixels):
        self._id = ImageSegment.id
        ImageSegment.id += 1
        self._label = label
        self._pixels = pixels
        self._border = Border([])

    def generate_border(self):
        starting_pixel = self._pixels[0]
        # find a pixel with a left border
        while (starting_pixel[0] - 1, starting_pixel[1]) in self._pixels:
            starting_pixel = (starting_pixel[0] - 1, starting_pixel[1])
        starting_direction = (0, 1)
        
        pixel = starting_pixel
        direction = starting_direction
        
        while(True):
            if pixel == (1, 0):
                pass
            right_hand = turn_right(direction)
            # if pixel to the right
            if tuple(map(operator.add, pixel, right_hand)) in self._pixels:
                # go there
                direction = right_hand
                pixel = tuple(map(operator.add, pixel, direction))
            else:
                vertex = tuple(map(operator.add, pixel, direction_to_corner(direction)))
                self._border.add_vertex(vertex)
                # turn left whilst marking edge until can go straight

                double_break = False
                while tuple(map(operator.add, pixel, direction)) not in self._pixels:
                    direction = turn_left(direction)
                    # exit
                    if pixel == starting_pixel and direction == starting_direction:
                        double_break = True
                        break
                    vertex = tuple(map(operator.add, pixel, direction_to_corner(direction)))
                    self._border.add_vertex(vertex)
                if double_break:
                    break
                # go straight
                pixel = tuple(map(operator.add, pixel, direction))
            # exit condition
            if pixel == starting_pixel and direction == starting_direction:
                break

    def refine_border(self, tolerance):
        area = len(self._pixels)  # since each pixel is area 1
        absolute_tolerance = tolerance * area
        self._border.refine(absolute_tolerance)

    @property
    def label(self):
        return self._label

    @property
    def pixels(self):
        return self._pixels
    
    @property
    def border(self):
        return self._border

    def __str__(self):
        return str(self._pixels)

def neighbours(point, image):
    width = image.width
    height = image.height
    result = []
    x, y = point
    if x != 0:
        result.append((x - 1, y))
    if x != width - 1:
        result.append((x + 1, y))
    if y != 0:
        result.append((x, y - 1))
    if y != height - 1:
        result.append((x, y + 1))
    return result

def image_segmentation(image):
    segments = []
    for y, row in enumerate(image):
        for x, pixel in enumerate(row):
            if pixel.segmented():
                continue
            # flood fill to define segment
            pixels = []
            nbs = neighbours((x, y), image)
            stack = [(x, y)]
            while len(stack) != 0:
                point = stack.pop()
                pixel = image[point[1]][point[0]]
                if not pixel.discovered():
                    pixel.set_discovered()
                    for nb in neighbours(point, image):
                        if pixel.color == image[nb[1]][nb[0]].color:
                            stack.append(nb)
                    pixels.append(point)
            segments.append(ImageSegment(pixel.color, pixels))
            for point in pixels:
                image[point[1]][point[0]].set_segmented()
    return segments
