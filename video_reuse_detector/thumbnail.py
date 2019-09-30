import cv2
import numpy as np

from dataclasses import dataclass

from video_reuse_detector import image_transformation, similarity


@dataclass
class Thumbnail:
    image: np.ndarray

    @staticmethod
    def from_image(image: np.ndarray, m=30):
        folded_grayscale = image_transformation.fold(
            image_transformation.normalized_grayscale(image, no_of_blocks=4))

        # Assume that converting the image to a m x m image is effectively
        # downsizing the image, hence interpolation=cv2.INTER_AREA
        im = cv2.resize(folded_grayscale, (m, m), interpolation=cv2.INTER_AREA)

        return Thumbnail(im)

    def similar_to(self, other: 'Thumbnail') -> float:
        return similarity.compare_images(self.image, other.image)


if __name__ == "__main__":
    import argparse
    from loguru import logger

    parser = argparse.ArgumentParser(
        description='Thumbnail creator')

    parser.add_argument(
        'image',
        help='An image to produce a thumbnail from')

    parser.add_argument(
        'output_path',
        help='Where to write the thumbnail')

    args = parser.parse_args()

    image_path = args.image
    logger.debug(f'Creating a thumbnail from "{image_path}". Destination={args.output_path}')  # noqa: E501

    th = Thumbnail.from_image(cv2.imread(image_path)).image
    cv2.imwrite(args.output_path, th)
