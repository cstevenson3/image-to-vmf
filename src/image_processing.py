import sys
from collections import namedtuple

import png
import drawSvg as draw

import operator
import vector


class Geometry:
    def __init__(self):
        self._segments = {}  # key id, value ImageSegment
        self._neighbours = {} # key id, value list of ids of neighbour ImageSegment's
    
    @property
    def segments(self):
        return self._segments

    @segments.setter
    def segments(self, value):
        self._segments = value

class ColorHSV(namedtuple('ColorHSV', 'h s v')):
    ''' HSV/HSB color format: hue, saturation, and brightness '''

    @staticmethod
    def almost_equal(chsv1, chsv2, threshold=0.05):
        h = abs((chsv1.h - chsv2.h + threshold) % 360 - threshold) < threshold
        s = abs(chsv1.s - chsv2.s) < threshold
        v = abs(chsv1.v - chsv2.v) < threshold
        return h and s and v

class Pixel:
    def __init__(self, color):
        assert isinstance(color, ColorHSV)
        self._color = color
        self._segmented = None

    @property
    def color(self):
        return self._color

    def discovered(self):
        return self._segmented is not None

    def set_discovered(self):
        self._segmented = False

    def set_segmented(self):
        self._segmented = True

    def segmented(self):
        return self._segmented is True

    def __repr__(self):
        return "Pixel({0:<3})".format(self._color)

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

def one_pixel_apart(p1, p2):
    return (p1[0] == p2[0] and abs(p1[1] - p2[1]) == 1) or (p1[1] == p2[1] and abs(p1[0] - p2[0]) == 1)

class Border:
    def __init__(self, vertices):
        self._vertices = vertices

    def add_vertex(self, vertex):
        self._vertices.append(vertex)
    
    def remove(self, vertex_index):
        self._vertices.pop(vertex_index)

    def area_change_on_removing(self, vertex_index):
        ''' negative for loss, positive for gain '''
        previous_vertex = self._vertices[(vertex_index - 1) % len(self._vertices)]
        vertex = self._vertices[vertex_index % len(self._vertices)]
        next_vertex = self._vertices[(vertex_index + 1) % len(self._vertices)]
        area_change = vector.cross(vector.subtract(previous_vertex, vertex), vector.subtract(next_vertex, vertex)) / float(2)
        return area_change


    def refine(self, tolerance):
        # delete middle points along lines
        i = 0
        while(True):
            n = len(self._vertices)
            if i >= n:
                break
            a, b, c = (self._vertices[i], self._vertices[(i + 1) % n], self._vertices[(i + 2) % n])
            if a[0] == b[0] == c[0] or a[1] == b[1] == c[1]:
                self.remove((i + 1) % n)
                continue
            i += 1

        # delete small corners
        i = 0
        while(True):
            n = len(self._vertices)
            if i >= n:
                break
            a, b, c = (self._vertices[i], self._vertices[(i + 1) % n], self._vertices[(i + 2) % n])
            if one_pixel_apart(a, b) or one_pixel_apart(b, c):
                if not vector.is_cc(a, b, c):
                    self.remove((i + 1) % n)
                    continue
            i += 1
        
        # tolerance based cleaning
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
                if abs(area_change) < best_area_change and area_change >= 0:  # only remove concavities and small protusions
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
    next_id = 0
    def __init__(self, label, pixels):
        self._id = ImageSegment.next_id
        ImageSegment.next_id += 1
        self._label = label
        self._pixels = pixels
        self._border = Border([])

    def pixel_in_grid(self, pixel):
        return self._grid_of_pixels[pixel[1]][pixel[0]]

    def bounds(self):
        ''' return (smallest_x, smallest_y, largest_x, largest_y) '''
        largest_x = 0
        largest_y = 0
        for pixel in self._pixels:
            if pixel[0] > largest_x:
                largest_x = pixel[0]
            if pixel[1] > largest_y:
                largest_y = pixel[1]
        return (0, 0, largest_x, largest_y)

    def generate_grid_of_pixels(self):
        _, _, largest_x, largest_y = self.bounds()

        self._grid_of_pixels = [[False for x in range(largest_x + 4)] for y in range(largest_y + 4)]  # 4 as margin of safety, not rigorous

        for pixel in self._pixels:
            self._grid_of_pixels[pixel[1]][pixel[0]] = True

    def generate_border(self):
        self.generate_grid_of_pixels()

        starting_pixel = self._pixels[0]
        # find a pixel with a left border
        while self.pixel_in_grid((starting_pixel[0] - 1, starting_pixel[1])):
            starting_pixel = (starting_pixel[0] - 1, starting_pixel[1])
        starting_direction = (0, 1)
        
        pixel = starting_pixel
        direction = starting_direction
        
        while(True):
            if pixel == (1, 0):
                pass
            right_hand = turn_right(direction)
            # if pixel to the right
            if self.pixel_in_grid(tuple(map(operator.add, pixel, right_hand))):
                # go there
                direction = right_hand
                pixel = tuple(map(operator.add, pixel, direction))
            else:
                vertex = tuple(map(operator.add, pixel, direction_to_corner(direction)))
                self._border.add_vertex(vertex)
                # turn left whilst marking edge until can go straight

                double_break = False
                while not self.pixel_in_grid(tuple(map(operator.add, pixel, direction))):
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
        self._border.vertices.reverse()

    def refine_border(self, tolerance):
        area = len(self._pixels)  # since each pixel is area 1
        absolute_tolerance = tolerance * area
        self._border.refine(absolute_tolerance)

    def print_border(self, filename):
        if(len(self.border.vertices) == 0):
            return
        _, _, largest_x, largest_y = self.bounds()
        d = draw.Drawing(largest_x + 4, largest_y + 4, origin=(0, 0), displayInline=False)
        v = self.border.vertices[:]
        xys = []
        for point in v:
            xys.append(point[0])
            xys.append(point[1])
        d.append(draw.Lines(*xys,
                        close=True,
                        fill='#ee0000',
                        stroke='black'))
        d.saveSvg(filename)

    @property
    def id(self):
        return self._id

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

def process_geometry(config, image):
    print("----Segmenting Image...")
    segments = image_segmentation(image)
    print("----Generating Borders...")
    for segment in segments:
        segment.generate_border()
    print("----Simplifying Borders...")
    i = 0
    for segment in segments:
        print("--------Simplifying Border...")
        segment.refine_border(0.001)
        # to inspect the segments being produced
        # segment.print_border(str(i) + ".svg")
        i += 1
    geometry = Geometry()
    for segment in segments:
        geometry.segments[segment.id] = segment
    return geometry
