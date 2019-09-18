import numpy as np
from typing import List


def bitfield(n: int) -> List[int]:
    return [1 if digit == '1' else 0 for digit in np.binary_repr(n)]


def hamming_distance(n1: int, n2: int) -> float:
    def H(v: List[int], u: List[int]) -> float:
        from scipy.spatial.distance import hamming

        return hamming(u, v)

    return H(bitfield(n1), bitfield(n2))


def normalized_crossed_correlation(qFp: np.ndarray, rFp: np.ndarray) -> float:
    left = qFp - np.mean(qFp)
    right = rFp - np.mean(rFp)
    dividend = np.sum(left*right)
    divisor = np.sqrt(np.sum(left**2) * np.sum(right**2))

    correlation = dividend / divisor

    return correlation


def compare_images(image1: np.ndarray, image2: np.ndarray) -> float:
    return normalized_crossed_correlation(image1, image2)
