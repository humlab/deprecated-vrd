import numpy as np


def hamming_distance(n1: int, n2: int) -> float:
    return bin(n1 ^ n2).count('1')/32.0


def normalized_crossed_correlation(qFp: np.ndarray, rFp: np.ndarray) -> float:
    left = qFp - np.mean(qFp)
    right = rFp - np.mean(rFp)
    dividend = np.sum(left*right)
    divisor = np.sqrt(np.sum(left**2) * np.sum(right**2))

    correlation = dividend / divisor

    return correlation


def compare_images(image1: np.ndarray, image2: np.ndarray) -> float:
    return normalized_crossed_correlation(image1, image2)
