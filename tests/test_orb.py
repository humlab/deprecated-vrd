import unittest
import skimage

from skimage import data
from skimage import transform as tf

from timeit import default_timer as timer

from video_reuse_detector.orb import ORB


class TestOrb(unittest.TestCase):

    def test_orb_self_similarity(self):
        astronaut = skimage.data.astronaut()

        orb = ORB.from_image(astronaut)

        # The ORB features of an image are 100% similar to itself
        naive = orb.similar_to_naive(orb)
        lu = orb.similar_to_lu(orb)

        self.assertEqual(naive, lu)

    def test_orb_similarity_rotation(self):
        img1 = skimage.img_as_ubyte(data.astronaut()).astype('uint8') * 255
        img2 = tf.rotate(img1, 180).astype('uint8')*255
        tform = tf.AffineTransform(scale=(1.3, 1.1), rotation=0.5,
                                   translation=(0, -200))
        img3 = tf.warp(img1, tform).astype('uint8') * 255

        orb1 = ORB.from_image(img1)
        orb2 = ORB.from_image(img2)
        orb3 = ORB.from_image(img3)

        start = timer()
        naive12 = orb1.similar_to_naive(orb2)
        end = timer()
        print(f'naive12 time: {end - start}')

        start = timer()
        naive13 = orb1.similar_to_naive(orb3)
        end = timer()
        print(f'naive13 time: {end - start}')
        self.assertEqual(naive12[1], naive13[1])

        start = timer()
        lu12 = orb1.similar_to_lu(orb2)
        end = timer()

        print(f'lu12 time: {end - start}')
        start = timer()
        lu13 = orb1.similar_to_lu(orb3)
        end = timer()
        print(f'lu13 time: {end - start}')
        self.assertEqual(lu12[1], lu13[1])

        self.assertEqual(naive12[1], lu12[1])
