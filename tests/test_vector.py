from src.vector import *

def test_is_cc():
    assert(is_cc((0, 0), (1, 0), (0, 1)))
    assert(not is_cc((0, 0), (0, 1), (1, 0)))
    assert(is_cc((0, 0), (1, 0), (-2, 1)))
    assert(not is_cc((0, 0), (1, 0), (0, -1)))
    assert(is_cc((2, 0), (-1, 3), (-1, 1)))
