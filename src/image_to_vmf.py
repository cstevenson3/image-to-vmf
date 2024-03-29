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
        self.scale = 1

    def __init__(self, json):
        self.color_mappings = {}
        for key in json["color_mappings"].keys():
            self.color_mappings[key] = ColorHSV(*json["color_mappings"][key])
        self.scale = json["scale"]

def import_config(filepath):
    f = open(filepath)
    config_json = json.loads(f.read())
    f.close()
    return Config(config_json)

def import_image(filepath):
    png_reader = png.Reader(filepath)
    width, height, rows, info = png_reader.read()
    dims = 4 if info["alpha"] else 3

    image = Image(width, height)

    for y, row in enumerate(rows):
        for x in range(width):
            r, g, b = (row[dims * x], row[dims * x + 1], row[dims * x + 2])
            r, g, b = (float(r) / 255, float(g) / 255, float(b) / 255)
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            # TODO, could convert back to integer values 
            # to ensure equality comparisons work
            color = ColorHSV(h, s, v)
            image[(height - 1) - y][x] = Pixel(color)
    return image

def main(args):
    print("Importing Image...")
    image = import_image("tests/test_data/output/output.png")

    config = import_config("tests/test_data/config.json")
    config.skybox_x = image.width
    config.skybox_y = image.height
    config.skybox_z = 512

    print("Processing Image...")
    geometry = process_geometry(config, image)

    print("Generating Structures...")
    map = generate_map(config, geometry)

    print("Building VMF...")
    vmf = VMF()
    vmf_body = generate_vmf_body(config, map)
    vmf_body.write(vmf)
    print(vmf.text)
    output = open("tests/test_data/output/output.vmf", "w")
    output.write(vmf.text)
    output.close()

if __name__ == "__main__":
    main(sys.argv)
