import operator

def subtract(a, b):
    if a == None or b == None:
        pass
    return tuple(map(operator.sub, a, b))

# 2D
def cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])

def is_cc(a, b, c):
    val = vector.cross(vector.subtract(b, a), vector.subtract(c, a))
    if val == 0:
        return None
    return val > 0

def is_intersect(p1, p2, q1, q2):
    dir1 = is_cc(p1, p2, q1)
    dir2 = is_cc(p1, p2, q2)
    dir3 = is_cc(q1, q2, p1)
    dir4 = is_cc(q1, q2, p2)
    return dir1 != dir2 and dir3 != dir4