import numpy


def average(images):
    # Assume all frames are of the same dimensions
    height, width, channels = images[0].shape

    avg = numpy.zeros((height, width, channels), numpy.float)

    for image in images:
        avg += image/len(images)

    return numpy.array(numpy.round(avg), dtype=numpy.uint8)