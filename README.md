# Overview

This project converts a hand sketched or computer drawn CS:GO layout into a VMF file editable and compilable in the Hammer map editor. See tests/test_data for examples of sketches (pencil on paper) and computer drawn layouts (blocked out colour).

Current colour config (colours must be exactly matched, use a color picker tool from the examples):
Red: wall
Green: floor
Yellow: bombsite
Blue: CT spawn
Orange: T spawn

Note that donut topologies (blocks of colour with islands of other colour within them) are not supported currently, leave a gap of black when a loop is formed.

Current text labelling config:

unlabelled: wall
XX: floor
ZZ: bombsite
HH: CT spawn
WW: T spawn

# Setup:

Install python 3 and pip for python 3

For the project:

pip3 install -r requirements.txt

OpenCV must be installed, use instructions here https://docs.opencv.org/master/df/d65/tutorial_table_of_content_introduction.html for your particular setup. If that doesn't work try others' solutions online.

# Run

To convert a sketched image into a blocked colour layout:

python3 src/sketch.py path/to/sketch_name.png

or to use the default test sketch:

python3 src/sketch.py 

This puts an output layout in tests/test_data/output/output.png


To convert a blocked colour layout into a vmf file:

python3 src/image_to_vmf.py path/to/layout_name.png

To use the output.png from sketch.py:

python3 src/image_to_vmf.py

This produces tests/test_data/output/output.vmf, which can be transferred to the Hammer SDK maps folder to be opened.

# Code

The two most relevant files are sketch.py and image_to_vmf.py. sketch.py handles hand sketched layouts, and image_to_vmf.py handles blocked colour layouts

## sketches

sketch.py contains the code relevant to interpreting the pencil in a hand sketched layout, looking for segments between them, and understanding the hand written labels. sketch.convolve_symbols handles template matching to look for handwritten letters. sketch.get_symbol accumulates the results of template matching at different scales, and looks for pairs of letters (which are used as text labels). sketch.get_pixel_regions finds pencil and solidifies thin parts so that segmentation is robust. sketch.get_black_segments flood fills between pencil to find distinct segments. sketch.main gets the text labels and segments from these functions, applies the text label colours to segments by flood fill, and fills gaps. 

## vmf creation

image_to_vmf.py imports the image and configuration, and coordinates the steps of converting a blocked colour layout into a map file.

image_processing.py flood fills and border walks to find the segments, their borders, and their labels. image_processing.image_segmentation flood fills to find pixels in each segment. image_processing.ImageSegment.generate_border does the border walk of a pixel segmentation to create a border. image_processing.Border.refine reduces the complexity of borders by removing unnecessary vertices (those that contribute excessively fine detail to the border). 

map_generation.py creates a general model of a map layout from the scanned objects

vmf_generation.py takes the general map model, and converts it into Source engine brushes, entities etc. vmf_generation.triangulate is the core of brush creation, where segment border polygons are triangulated so convex brushes can be made.

## other

sketch_ocr.py is an adaptation of https://www.pyimagesearch.com/2018/09/17/opencv-ocr-and-text-recognition-with-tesseract/, to test if common OCR methods worked for this application. They did not but it's a useful reference. Running this requires installing tesseract for python.

