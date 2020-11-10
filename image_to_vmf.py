from enum import Enum

from image_processing import *
from vmf_generation import *

class SegmentType(Enum):
    ''' What blocks of colour map to: floors, walls etc. '''
    FLOOR, WALL = range(2)

class Config:
    def __init__(self):
        self._color_mappings = {}  # key , value 

def main(args):
    png_reader = png.Reader("tests/example.png")
    width, height, rows, info = png_reader.read()

    image = Image(width, height)

    for y, row in enumerate(rows):
        for x in range(width):
            color = ColorHSV(row[4 * x], row[4 * x + 1], row[4 * x + 2])
            image[y][x] = Pixel(color)
    
    segments = image_segmentation(image)
    for segment in segments:
        segment.generate_border()
        print(segment.border)
        print("refining border...")
        segment.refine_border(0.1)
        print(segment.border)
        print()
        print()

    vmf = VMF()
    # for segment in segments:
    #     GIS = csgo.build_object(segment)
    #     GIS.add_to_map(vmf)
    vmf_body = VMFBody()
    vmf_body.write(vmf)
    print(vmf.text)

if __name__ == "__main__":
    main(sys.argv)
