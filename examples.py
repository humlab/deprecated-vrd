from pathlib import Path

from skimage import data, img_as_ubyte
from main import produce_normalized_grayscale_image, produce_thumbnail, keyframe, fold, imwrite
from image_transformation import grayscale

images = {
    'astronaut': data.astronaut(),
    'chelsea': data.chelsea(),
    'coffee': data.coffee(),
    'rocket': data.rocket(),
}

for name, image in images.items():
    cv_image = img_as_ubyte(image)

    output_directory = Path('examples')
    imwrite(output_directory / f'{name}-thumb.png', produce_thumbnail(cv_image))
    imwrite(output_directory / f'{name}-grayscale.png', grayscale(cv_image))
    imwrite(output_directory / f'{name}-normalized-grayscale.png', produce_normalized_grayscale_image(cv_image))
    imwrite(output_directory / f'{name}-fold.png', fold(cv_image))
