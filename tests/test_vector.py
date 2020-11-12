from src.vector import *

def test_is_cc():
    assert(is_cc((0, 0), (1, 0), (0, 1)))
    assert(not is_cc((0, 0), (0, 1), (1, 0)))
    assert(is_cc((0, 0), (1, 0), (-2, 1)))
    assert(not is_cc((0, 0), (1, 0), (0, -1)))
    assert(is_cc((2, 0), (-1, 3), (-1, 1)))

def test_cross():
    assert(cross((4,5), (6,7)) == -2)
    assert(cross((4.0,5.0), (6.0,7.0)) == -2.0)

def test_is_intersect():
    assert(is_intersect((2,2), (-2, -1), (-1, 1), (1, -1)))
    assert(not is_intersect((2,2), (-2, 2), (-1, -1), (1, -1)))