from enum import Enum

import colorsys

from image_processing import *
from map_generation import *
from vmf_generation import *

class SegmentType(Enum):
    ''' What blocks of colour map to: floors, walls etc. '''
    FLOOR, WALL = range(2)

class Config:
    def __init__(self):
        self._color_mappings = {}  # key ColorHSV, value SegmentType

def main(args):
    png_reader = png.Reader("tests/example.png")
    width, height, rows, info = png_reader.read()

    image = Image(width, height)

    for y, row in enumerate(rows):
        for x in range(width):
            h, s, v = colorsys.rgb_to_hsv(row[4 * x], row[4 * x + 1], row[4 * x + 2])
            color = ColorHSV(h, s, v)
            image[y][x] = Pixel(color)

    geometry = process_geometry(config, image)

    map = generate_map(config, geometry)

    vmf = VMF()
    vmf_body = generate_vmf(config, map)
    vmf_body.write(vmf)
    print(vmf.text)

if __name__ == "__main__":
    main(sys.argv)
