

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


