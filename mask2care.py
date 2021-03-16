"""
    Class supporting the creation of a simple API endpoint
"""
import os, cv2, dlib, io, numpy as np
import cloudinary.uploader
from PIL import Image
from urllib.request import urlopen
from dotenv import load_dotenv

class Mask2Care():
    def __init__(self):
        self.lstReturnedItems = list()
        self.imgBuffer = io.BytesIO()
        self.server_root = os.path.dirname(os.path.abspath(__file__))

        project_folder = os.path.expanduser('/users/brad/code/mask2careapi')  # ON WEB SERVER: ~/mask2careapi
        load_dotenv(os.path.join(project_folder, '.env'))

        # Secret stuff here ...
        self.cloudinary_config = cloudinary.config(
            cloud_name = os.getenv("CLOUDNAME"),
            api_key = os.getenv("APIKEY"),
            api_secret = os.getenv("APISECRET")
        )
        return

    def __del__(self):
        del self.lstReturnedItems
        del self.imgBuffer
        del self.cloudinary_config
        del self.server_root
        return

    def __urlToImage(self, url, readFlag=cv2.IMREAD_COLOR):
        # download the image, convert it to a NumPy array, and then read it into an OpenCV format
        resp = urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, readFlag)

        return image

    def simpleTest(self):
        img = Image.open(os.path.join(self.server_root, "static", "maskTemplate01.png"))
        self.imgBuffer.seek(0)
        img.save(self.imgBuffer, format="PNG")
        self.imgBuffer.seek(0)
        response = cloudinary.uploader.upload(self.imgBuffer)
        return response["url"]

    def getOrderOptions(self, strSelfieImageURL):
        """
            input: strSelfieImageURL is the URL to the selfie taken with the mobile device's camera
            returns: list of images saved within MediaDB database
        """
        d = dict()
        self.lstReturnedItems = list()
        d["items"] = self.lstReturnedItems
        d["error"] = "ok"  # all good!

        if strSelfieImageURL and strSelfieImageURL != "":
            img = self.__urlToImage(strSelfieImageURL)
            img = cv2.resize(img, (0,0), fx=0.5, fy=0.5)   # half the size of the image
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # now set up the dlib model
            modelPathFn = os.path.join(self.server_root, "static", "shape_predictor_68_face_landmarks.dat")
            frontalFaceDetector = dlib.get_frontal_face_detector()
            faceLandmarkDetector = dlib.shape_predictor(modelPathFn)

            # start facial and landscape detection
            allFaces = frontalFaceDetector(imgRGB, 0)
            if len(allFaces) > 0:  # we found a face ...
                # print("We found a face ...")
                face = allFaces[0]  # just use the first face
                faceRectDlib = dlib.rectangle(int(face.left()), int(face.top()), int(face.right()), int(face.bottom()))
                detectedLandmarks = faceLandmarkDetector(imgRGB, faceRectDlib)
                lm = detectedLandmarks.parts()
                if (len(lm) > 60):   # we found landmarks on the face
                    # print("We have the landmarks ...")
                    tip_chin = lm[8]
                    top_nose = lm[27]
                    right_jaw = lm[16]
                    left_jaw = lm[0]

                    # now deal with overlaying the image, using the PIL module for that
                    wOVL = right_jaw.x - left_jaw.x
                    hOVL = tip_chin.y - top_nose.y

                    xOVL = left_jaw.x
                    yOVL = top_nose.y

                    for i in range(1, 7):  # we have six design options with our assets folder ...
                        imgOVL = Image.open(os.path.join(self.server_root, "static", "maskTemplate0{}.png".format(i)))
                        imgOVL = imgOVL.resize((wOVL, hOVL))  # resize based upon facial landmarks
                        imgOVL = imgOVL.convert("RGBA")  # enable transparency within overlayed image
                        imgMain = Image.fromarray(imgRGB)  # converting a CV2 image to PIL format
                        imgMain.paste(imgOVL, (xOVL, yOVL), imgOVL)

                        self.imgBuffer.seek(0)
                        imgMain.save(self.imgBuffer, format="JPEG")
                        self.imgBuffer.seek(0)
                        response = cloudinary.uploader.upload(self.imgBuffer)

                        if response:
                            self.lstReturnedItems.append(response["url"])
                else:
                    d["error"] = "Can not identify facial landscapes, please retry"
            else:
                d["error"] = "Can not find a face, please retry"

        d["items"] = self.lstReturnedItems

        return d


if __name__ == '__main__':
    """
        Some testing going on here ...
    """
    obj = Mask2Care()
    d = obj.getOrderOptions("https://res.cloudinary.com/dpeqsj31d/image/upload/v1615415661/BradGreenSquarePostIt01.jpg")
    print("returned: {}".format(d))
