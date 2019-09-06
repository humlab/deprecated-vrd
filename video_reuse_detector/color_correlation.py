import numpy as np

from video_reuse_detector import util

RGB = 'rgb'
RBG = 'rbg'
GRB = 'grb'
GBR = 'gbr'
BRG = 'brg'
BGR = 'bgr'

correlation_cases = [RGB, RBG, GRB, GBR, BRG, BGR]


def avg_intensity_per_color_channel(block):
    avg_color_per_row = np.average(block, axis=0)
    avg_intensity_per_channel = np.average(avg_color_per_row, axis=0)

    assert(len(avg_intensity_per_channel) == 3)  # Three channels

    return tuple(avg_intensity_per_channel)


def color_transformation_and_block_splitting(image, nr_of_blocks=16):
    im_h, im_w = image.shape[:2]
    bl_h, bl_w = util.compute_block_size(image, nr_of_blocks)

    # A new image that is a downsampling of the original where the average
    # intensities of each block are stored, i.e. consider the top-most left
    # block of our original image, then the first element in this matrix will
    # be the average intensity (per channel) of that block,
    average_intensities = np.zeros((bl_h, bl_w, 3))

    row_offset = int(round(bl_h/nr_of_blocks))
    col_offset = int(round(bl_w/nr_of_blocks))

    # Process the original image in blocks of our established sizes,
    for row in np.arange(im_h - bl_h + 1, step=bl_h):
        for col in np.arange(im_w - bl_w + 1, step=bl_w):
            block_to_process = image[row:row+bl_h, col:col+bl_w]
            avgs = avg_intensity_per_color_channel(block_to_process)

            # The index of the block which we just processed,
            block_row_idx = int(round(row/bl_h))
            assert(block_row_idx < nr_of_blocks)
            block_col_idx = int(round(col/bl_w))
            assert(block_col_idx < nr_of_blocks)

            # The index in the new, downsampled, image called
            # "average_intensities", where our result "avgs" will go,
            r = block_row_idx * row_offset
            c = block_col_idx * col_offset

            average_intensities[r:r+row_offset, c:c+col_offset] = avgs

    return average_intensities


def trunc(number, significant_decimals=2):
    """Truncates the given number to significant_decimals number of decimals

    As per Lei et al., Section II.B step 3, i.e. "Quantization and Feature
    Representation", each value is truncated to two significant digits
    (decimal places), hence the default value for significant_decimals
    """
    # https://stackoverflow.com/a/37697840/5045375
    import math

    d = significant_decimals
    stepper = 10.0 ** d
    return math.trunc(round(stepper * number, d * 3)) / stepper


def feature_representation(cc_histogram):
    cc_bin = ""

    # Will this be the same iteration order if we just iterate over the values?
    # TODO: Explore how slow this is and if a bitshift-dance is appropriate
    for _, value in cc_histogram.items():
        cc_bin += format(int(trunc(value) * 100), '07b')

    cc_bin = cc_bin[7:]
    assert(len(cc_bin) == 35)

    return int(cc_bin, 2)


def color_correlation_histogram(image):
    import collections
    cc = collections.OrderedDict({
        RGB: 0,
        RBG: 0,
        GRB: 0,
        GBR: 0,
        BRG: 0,
        BGR: 0
    })

    for row in image:
        for pixel in row:
            # OpenCV images are represented as a 3D numpy ndarray. The
            # first two axes represent the pixel matrix.
            #
            # The third axis (Z) contains the color channels (B,G,R), not
            # (r,g,b).
            blue = pixel[0]
            green = pixel[1]
            red = pixel[2]

            if red == green == blue:
                # As per "Video Sequence Matching Based on the Invariance
                # of Color Correlation" (Lei et al. 2012)
                # Section II.B this case is ignored,
                pass
            elif red >= green >= blue:
                cc[RGB] += 1
            elif red >= blue >= green:
                cc[RBG] += 1
            elif green >= red >= blue:
                cc[GRB] += 1
            elif green >= blue >= red:
                cc[GBR] += 1
            elif blue >= red >= green:
                cc[BRG] += 1
            elif blue >= green >= red:
                cc[BGR] += 1

    processed_pixels = sum(cc.values())

    # Normalize the histogram,
    if processed_pixels > 0:
        normalized_cc = {k: v/processed_pixels for (k, v) in cc.items()}

        # Sanity-check
        np.testing.assert_almost_equal(sum(normalized_cc.values()), 1.0)

        assert(all(0 <= v and v <= 1.0 for v in normalized_cc.values()))
    else:
        normalized_cc = {k: 0 for (k, _) in cc.items()}

    return normalized_cc


def color_correlation(image, nr_of_blocks=16):
    color_avgs = color_transformation_and_block_splitting(image, nr_of_blocks)
    return color_correlation_histogram(color_avgs)
