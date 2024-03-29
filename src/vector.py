import operator

def subtract(a, b):
    if a == None or b == None:
        pass
    return tuple(map(operator.sub, a, b))

def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]

def is_cc(a, b, c):
    val = cross(subtract(b, a), subtract(c, a))
    return val >= 0

def segments_intersect(segment_1, segment_2):
    return is_intersect(segment_1[0], segment_1[1], segment_2[0], segment_2[1])

def is_intersect(p1, p2, q1, q2):
    if not len(set([p1, p2]).intersection(set([q1, q2]))) == 0:
        return False
    dir1 = is_cc(p1, p2, q1)
    dir2 = is_cc(p1, p2, q2)
    dir3 = is_cc(q1, q2, p1)
    dir4 = is_cc(q1, q2, p2)
    return dir1 != dir2 and dir3 != dir4

def point_in_triangle(point, triangle):
    if point in triangle:
        return False
    left_0 = is_cc(triangle[0], triangle[1], point)
    left_1 = is_cc(triangle[1], triangle[2], point)
    left_2 = is_cc(triangle[2], triangle[0], point)
    return left_0 and left_1 and left_2