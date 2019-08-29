import numpy as np
import cv2


def average(images):
    # Assume all images are of the same dimensions
    height, width, channels = images[0].shape

    avg = np.zeros((height, width, channels), np.float)

    for image in images:
        avg += image/len(images)

    return np.array(np.round(avg), dtype=np.uint8)


def interpolation_method(scale_factor):
    # Another option for upscaling is INTER_CUBIC which is slower but
    # produces a better looking output. Using INTER_LINEAR for now
    return cv2.INTER_LINEAR if scale_factor >= 1 else cv2.INTER_AREA


def scale(image, scale_factor):
    height, width, _ = image.shape
    new_height, new_width = int(height*scale_factor), int(width*scale_factor)
    interpolation = interpolation_method(scale_factor)

    return cv2.resize(image, (new_height, new_width), interpolation)


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
