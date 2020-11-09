import operator

def subtract(a, b):
    if a == None or b == None:
        pass
    return tuple(map(operator.sub, a, b))

# 2D
def cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])