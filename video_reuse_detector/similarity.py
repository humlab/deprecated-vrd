import numpy as np
from typing import List


def bitfield(n: int) -> List[int]:
    return [1 if digit == '1' else 0 for digit in np.binary_repr(n)]


def hamming_distance(n1: int, n2: int) -> float:
    def H(v: List[int], u: List[int]) -> float:
        from scipy.spatial.distance import hamming

        return hamming(u, v)

    return H(bitfield(n1), bitfield(n2))
