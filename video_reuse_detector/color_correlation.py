RGB = 'rgb'
RBG = 'rbg'
GRB = 'grb'
GBR = 'gbr'
BRG = 'brg'
BGR = 'bgr'


def color_correlation(image, block_size=(16, 16)):
    def color_correlation(block):
        import collections
        cc = collections.OrderedDict({
            RGB: 0,
            RBG: 0,
            GRB: 0,
            GBR: 0,
            BRG: 0,
            BGR: 0
        })

        for row in block:
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
                    # of Color Correlation" Section II.B these are ignored
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
        normalized_cc = {k: v/processed_pixels for (k, v) in cc.items()}

        # Sanity-check
        assert(sum(normalized_cc.values()) == 1)
        return normalized_cc

    # TODO: Split image into blocks
    return color_correlation(image)
