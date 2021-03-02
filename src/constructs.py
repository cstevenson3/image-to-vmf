from vmf_objects import Brush, Side

def hollow_box(left, right, bottom, top, lower, upper, thickness=16):
    ''' returns a list of Brushes forming a hollow box 
    with inner dimensions according to the given parameters '''
    left_wall = block(left - thickness, left, bottom, top, lower, upper)
    right_wall = block(right, right + thickness, bottom, top, lower, upper)
    bottom_wall = block(left, right, bottom - thickness, bottom, lower, upper)
    top_wall = block(left, right, top, top + thickness, lower, upper)
    floor = block(left, right, bottom, top, lower - thickness, lower)
    ceiling = block(left, right, bottom, top, upper, upper + thickness)
    return [left_wall, right_wall, bottom_wall, top_wall, floor, ceiling]

def block(left, right, bottom, top, lower, upper):
    ''' returns a rectangular prism Brush '''
    left_plane = [(left, bottom, lower), (left, top, lower), (left, top, upper)]
    right_plane = [(right, bottom, lower), (right, bottom, upper), (right, top, upper)]
    bottom_plane = [(left, bottom, lower), (left, bottom, upper), (right, bottom, upper)]
    top_plane = [(left, top, lower), (right, top, lower), (right, top, upper)]
    lower_plane = [(left, bottom, lower), (right, bottom, lower), (right, top, lower)]
    upper_plane = [(left, bottom, upper), (left, top, upper), (right, top, upper)]
    return Brush([Side(left_plane), Side(right_plane), Side(bottom_plane), Side(top_plane), Side(lower_plane), Side(upper_plane)])