import cv2
import numpy as np

from dataclasses import dataclass

from video_reuse_detector import image_transformation, util, similarity


def map_over_blocks(image, f, nr_of_blocks=16):
    block_img = np.zeros(image.shape)
    im_h, im_w = image.shape[:2]
    bl_h, bl_w = util.compute_block_size(image, nr_of_blocks)

    for row in np.arange(im_h - bl_h + 1, step=bl_h):
        for col in np.arange(im_w - bl_w + 1, step=bl_w):
            block_to_process = image[row:row+bl_h, col:col+bl_w]
            block_img[row:row+bl_h, col:col+bl_w] = f(block_to_process)

    return block_img


def normalized_grayscale(image: np.ndarray) -> np.ndarray:
    def zscore(block):
        mean = np.mean(block)
        std = np.std(block)
        return mean - std

    return map_over_blocks(image_transformation.grayscale(image), zscore)


@dataclass
class Thumbnail:
    image: np.ndarray

    @staticmethod
    def from_image(image: np.ndarray, m=30):
        grayscale = normalized_grayscale(image)
        folded_grayscale = image_transformation.fold(grayscale)

        # Assume that converting the image to a m x m image is effectively
        # downsizing the image, hence interpolation=cv2.INTER_AREA
        im = cv2.resize(folded_grayscale, (m, m), interpolation=cv2.INTER_AREA)

        return Thumbnail(im)

    def similar_to(self, other: 'Thumbnail') -> float:
        return similarity.compare_images(self.image, other.image)
