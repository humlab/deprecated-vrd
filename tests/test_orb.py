import unittest
import skimage

from skimage import data
from skimage import transform as tf

from video_reuse_detector.orb import ORB


class TestOrb(unittest.TestCase):

    def test_orb_self_similarity(self):
        astronaut = skimage.data.astronaut()

        orb = ORB.from_image(astronaut)

        # The ORB features of an image are 100% similar to itself
        self.assertEqual(orb.similar_to_lu(orb), orb.similar_to_lu(orb))

    def test_orb_similarity_rotation(self):
        img1 = skimage.img_as_ubyte(data.astronaut()).astype('uint8') * 255
        img2 = tf.rotate(img1, 180).astype('uint8')*255
        tform = tf.AffineTransform(scale=(1.3, 1.1), rotation=0.5,
                                   translation=(0, -200))
        img3 = tf.warp(img1, tform).astype('uint8') * 255

        orb1 = ORB.from_image(img1)
        orb2 = ORB.from_image(img2)
        orb3 = ORB.from_image(img3)

        lu12 = orb1.similar_to_lu(orb2)
        lu13 = orb1.similar_to_lu(orb3)
        self.assertEqual(lu12[1], lu13[1])
