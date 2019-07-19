from __future__ import print_function
import pyzbar.pyzbar as pyzbar
import numpy as np
from PIL import Image
import re
import io
import base64, json
import cv2



def decode(url):
    # Find barcodes and QR codes

    imgstr = re.search(r'base64,(.*)', url).group(1)
    image_bytes = io.BytesIO(base64.b64decode(imgstr))
    im = Image.open(image_bytes)
    im = im.convert('1')
    im = np.array(im)
    #im = binarize_array(im, 200)
    #print("this is the image sent to pyzbar")
    #print(im)
    decodedObjects = pyzbar.decode(im)
    #print("this is the decoded data"+decodedObjects)


    # return decodedObjects.Decoded
    # Print results
    data = []

    for obj in decodedObjects:
        print('Type : ', obj.type)
        print('Data : ', obj.data, '\n')
        data.append({
            "code":obj.data.decode('utf-8') ,
            "type": obj.type
        })
        # return "Code: "+code.decode('utf-8') + "\nType: "+ types
    #data = serializers.serialize('json', data)
    print(data)
    return data


def binarize_array(numpy_array, threshold=200):
    """Binarize a numpy array."""
    for i in range(len(numpy_array)):
        for j in range(len(numpy_array[0])):
            if numpy_array[i][j] > threshold:
                numpy_array[i][j] = 255
            else:
                numpy_array[i][j] = 0
    return numpy_array
