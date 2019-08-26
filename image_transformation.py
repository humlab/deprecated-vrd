import numpy
import cv2


def average(images):
    # Assume all images are of the same dimensions
    height, width, channels = images[0].shape

    avg = numpy.zeros((height, width, channels), numpy.float)

    for image in images:
        avg += image/len(images)

    return numpy.array(numpy.round(avg), dtype=numpy.uint8)


def scale(image, scale_factor):
    height, width, _ = image.shape

    # Another option for upscaling is INTER_CUBIC which is slower but
    # produces a better looking output. Using INTER_LINEAR for now
    interpolation_method = cv2.INTER_LINEAR if scale_factor >= 1 else cv2.INTER_AREA
    return cv2.resize(image, (int(width*scale_factor), int(height*scale_factor)), interpolation=interpolation_method)


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)