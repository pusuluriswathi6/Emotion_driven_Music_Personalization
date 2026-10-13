from django.conf import settings
from PyEmotion import *
import cv2 as cv
class ImageExpressionDetect:
    def getExpression(self,imagepath):
        filepath = settings.MEDIA_ROOT + "\\" + imagepath
        PyEmotion()
        er = DetectFace(device='cpu', gpu_id=0)
        # Open you default camera
        # img = cv.imread('test.jpg')
        # cap = cv.VideoCapture(0)
        # ret, frame = cap.read()
        frame, emotion = er.predict_emotion(cv.imread(filepath))
        cv.imshow('EM & MPS', frame)
        cv.waitKey(0)
        print("Hi",filepath,"Emotion is ",emotion)
        return emotion

    def getLiveDetect(self):
        print("Streaming Started")
        PyEmotion()
        er = DetectFace(device='cpu', gpu_id=0)
        # Open you default camera
        cap = cv.VideoCapture(0)
        emotions_count = {}
        while (True):
            ret, frame = cap.read()
            frame, emotion = er.predict_emotion(frame)

            if emotion in emotions_count:
                emotions_count[emotion] += 1
            else:
                emotions_count[emotion] = 1

            print("Detected Emotion:", emotion)
            cv.imshow('Press Q to Exit', frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv.destroyAllWindows()

        most_repeated_emotion = max(emotions_count, key=emotions_count.get)
        print("Most Repeated Emotion:", most_repeated_emotion)
        return most_repeated_emotion
