def compute_block_size(image, nr_of_blocks=16):
    height, width = image.shape[:2]
    block_height = int(round(height / nr_of_blocks))
    block_width = int(round(width / nr_of_blocks))

    return (block_height, block_width)
