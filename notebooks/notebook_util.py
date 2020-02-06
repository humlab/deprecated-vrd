def rgb(image):
    import cv2
    
    # Convert the numpy array to uint8 as to be able to convert the color
    cv2_compatible_image = image.astype('uint8')

    # OpenCV images are in BGR, meanwhile pyplot expects RGB,
    rgb_image = cv2.cvtColor(cv2_compatible_image, cv2.COLOR_BGR2RGB)

    return rgb_image
