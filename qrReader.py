import cv2
import numpy as np
import sys
import time
from pyzbar.pyzbar import decode
#from PIL import Image, ImageDraw

class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        #self.is_record = False
        self.video = cv2.VideoCapture(-1)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()

    def closeCam(self):
        self.video.release()
		
	
    def get_frame(self):
        #self.is_record=True
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        return image
	
    def gen(self):
        while True:
            #frame = camera.get_frame()
            img2 = self.get_frame()  
            gray=cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)          
            imageData=decode(gray)
            #print(imageData)
            ############################
            if len(imageData) > 0:            
                data=[]
                for barcode in imageData:            
                    data.append(barcode.data)
                    rect = barcode.rect                    
                    img2=cv2.rectangle(img2,(rect.left,rect.top),(rect.left+rect.width,rect.top+rect.height),(0,255,0),3)     
                    ret, jpeg = cv2.imencode('.jpg', img2)          
                #print(data)       #we've to feed this data to the server db 
            else:        			
                ret, jpeg = cv2.imencode('.jpg', img2)
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            #if key==ord('q'):
             #   break

    def start_record(self):
        self.is_record = True


    def stop_quiz(self):
        self.is_record = False
