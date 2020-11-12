from enum import Enum

import colorsys
import json

from image_processing import *
from map_generation import *
from vmf_generation import *

class SegmentType(Enum):
    ''' What blocks of colour map to: floors, walls etc. '''
    FLOOR, WALL = range(2)

class Config:
    ''' Usually initialised from a file '''
    def __init__(self):
        self.color_mappings = {}  # key ColorHSV, value SegmentType

    def __init__(self, json):
        pass

def import_config(filepath):
    f = open(filepath)
    config_json = json.loads(f.read())
    f.close()
    return Config(config_json)

def import_image(filepath):
    png_reader = png.Reader(filepath)
    width, height, rows, info = png_reader.read()

    image = Image(width, height)

    for y, row in enumerate(rows):
        for x in range(width):
            h, s, v = colorsys.rgb_to_hsv(row[4 * x], row[4 * x + 1], row[4 * x + 2])
            color = ColorHSV(h, s, v)
            image[(height - 1) - y][x] = Pixel(color)
    return image

def main(args):
    config = import_config("tests/test_data/config.json")
    image = import_image("tests/test_data/example.png")

    geometry = process_geometry(config, image)

    map = generate_map(config, geometry)

    vmf = VMF()
    vmf_body = generate_vmf(config, map)
    vmf_body.write(vmf)
    print(vmf.text)
    output = open("tests/output.vmf", "w")
    output.write(vmf.text)
    output.close()

if __name__ == "__main__":
    main(sys.argv)
