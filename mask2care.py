"""
    Class supporting the creation of a simple API endpoint
"""
import os, cv2, dlib, io, math, numpy as np
import cloudinary.uploader
from PIL import Image
from urllib.request import urlopen
from operator import itemgetter
from dotenv import load_dotenv
from maskpatternprint import MaskPatternPrint

class Mask2Care():
    def __init__(self):
        self.lstReturnedItems = list()
        self.imgBuffer = io.BytesIO()
        self.server_root = os.path.dirname(os.path.abspath(__file__))
        self.objPattern = MaskPatternPrint()

        project_folder = os.path.expanduser(self.server_root)  # ON WEB SERVER: ~/mask2careapi
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
        del self.objPattern
        return

    def __urlToImage(self, url, readFlag=cv2.IMREAD_COLOR):
        # download the image, convert it to a NumPy array, and then read it into an OpenCV format
        resp = urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, readFlag)

        return image

    def getMaskPattern(self, strSelfieImageURL):
        """
            input: strSelfieImageURL is the URL to the selfie taken with the mobile device's camera
            returns: URL of the pdf file representing the mask pattern
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
                    left_eye = lm[36]
                    right_eye = lm[45]
                    eye_spacing = right_eye.x - left_eye.x
                    top_y = max(left_eye.y, right_eye.y) - eye_spacing  # min is the "higher" eye

                    stickynote = imgRGB[int(top_y):right_eye.y, left_eye.x:right_eye.x]
                    gray = cv2.cvtColor(stickynote, cv2.COLOR_BGR2GRAY)
                    ret, thresh = cv2.threshold(gray, 200, 255, 0)
                    thresh = cv2.GaussianBlur(thresh, (3, 3), 0)  # (7,7), 1.4)

                    hull = None
                    boolFound = False
                    contours, hier = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                    for cnt in contours:
                        if cv2.contourArea(cnt) > 5000:  # remove small areas like noise etc
                            hull = cv2.convexHull(cnt)  # find the convex hull of contour
                            hull = cv2.approxPolyDP(hull, 0.1 * cv2.arcLength(hull, True), True)
                            if len(hull) == 4:
                                cv2.drawContours(stickynote, [hull], 0, (0, 255, 0), 2)
                                boolFound = True
                                break

                    if boolFound:
                        # print("We have the stickynote ...")
                        hull = hull.reshape(-1, 2)
                        coordinates = list()
                        for item in hull:
                            coordinates.append(tuple(item))

                        coordinates = sorted(coordinates, key=itemgetter(1)) # sort by y so coordinates 3,4 are bottom edges of postit
                        # print(coordinates)

                        hypotenuse = pow((coordinates[3][1] - coordinates[2][1]), 2) + pow((coordinates[3][0] - coordinates[2][0]), 2)

                        pixelsPerCm = math.sqrt(hypotenuse) / 5.0
                        # print("Pixels per centimeter in halved file: {}".format(pixelsPerCm))  # need to user grab the "5.0" - width of the postit note

                        tip_chin = lm[8]
                        top_nose = lm[27]
                        tip_nose = lm[34]

                        # Chin to neck  using 1/2 distance between eyes as proxy
                        hypotenuse = math.sqrt(pow((right_eye.y - left_eye.y), 2) + pow((right_eye.x - left_eye.x), 2))
                        # print("distance between eyes (px): {} (cm): {}".format(hypotenuse, hypotenuse / pixelsPerCm))
                        chin_to_neck = (hypotenuse / pixelsPerCm) / 2.0

                        # jawbones
                        left_jaw = lm[0]
                        right_jaw = lm[16]
                        jawbones = math.sqrt(pow((right_jaw.y - left_jaw.y), 2) + pow((right_jaw.x - left_jaw.x), 2))
                        ovalCir = math.pi * math.sqrt(2.0 * (pow(jawbones / 2.0, 2) + pow(jawbones / 2.0, 2)))
                        # using 60% as an unsupported estimate of the proportion of the circumference of the head (looking top down)
                        # representing tip of ears to tip of ears including tip of nose

                        # nose length
                        hypotenuse = math.sqrt(pow((tip_nose.y - top_nose.y), 2) + pow((tip_nose.x - top_nose.x), 2))

                        # print("maskPrint args:{}, {}, {}".format(chin_to_neck, (ovalCir * 0.6) / pixelsPerCm, (hypotenuse / pixelsPerCm)))
                        d["items"] = self.objPattern.maskPrint(chin_to_neck, (ovalCir * 0.6) / pixelsPerCm, (hypotenuse / pixelsPerCm))

                    else:
                        d["error"] = "Can not identify stickynote, please retry."
                else:
                    d["error"] = "Can not identify facial landscapes, please retry."
            else:
                d["error"] = "Can not find a face, please retry."

        return d

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
    # d = obj.getOrderOptions("https://res.cloudinary.com/dpeqsj31d/image/upload/v1615415661/BradGreenSquarePostIt01.jpg")
    d = obj.getMaskPattern("https://res.cloudinary.com/dpeqsj31d/image/upload/v1615584133/BradWhiteSquarePostIt01.jpg")
    del obj
    print("returned: {}".format(d))
