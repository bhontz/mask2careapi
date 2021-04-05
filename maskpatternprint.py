"""
    maskPrint.py    2/22/21
    Creates a PDF pattern of a three piece mask based upon this design:
    https://singer.com.hk/blogs/sewing-projects/how-to-make-face-mask
    Arguments obtained from facial landscaping: noseLength, jawBones, chinToNeck
    The three arguments are assumed to be in floats and in cm units
    reportlab module is used to render the PDF, see: https://www.reportlab.com/docs/reportlab-userguide.pdf
"""
import os, sys, io, time
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import cloudinary.uploader
from dotenv import load_dotenv

class MaskPatternPrint():
    def __init__(self):
        self.server_root = os.path.dirname(os.path.abspath(__file__))
        self.imgBuffer = io.BytesIO()

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
        del self.server_root
        del self.imgBuffer
        del self.cloudinary_config

        return

    def __drawGrid(self, c):
        """
            Draw grid lines on the canvas
        """
        c.saveState()
        try:
            c.setStrokeColorRGB(152 / 255, 251 / 255, 152 / 255)
            c.setLineWidth(1)
            c.setDash(1, 2)

            # Draw horizontal
            for i in range(1, 29):
                c.line(0, -cm * i, 21 * cm, -cm * i)

            # Draw vertical
            for i in range(1, 21):
                c.line(i * cm, 0, i * cm, -28 * cm)

        finally:
            c.restoreState()

        return

    def __drawLabel(self, c, x, y, str):
        """
            Draw a label on the canvas
        """
        c.saveState()
        try:
            c.translate(x, y)
            c.rotate(180)
            textObj = c.beginText(x, y)
            textObj.setFont('Times-Roman', 12)
            textObj.setFillColorRGB(50/255, 50/255, 255/255)
            textObj.textLine(text = str)
            # c.rotate(90)
            c.drawText(textObj)

            # c.drawString(x, y, str)

        finally:
            c.restoreState()

        return

    def __drawChin(self, c, x, y, w, h):
        """
            draw chin bounding rectangle
        """
        c.saveState()
        try:
            c.setStrokeColorRGB(50/255, 50/255, 255/255)
            # c.rect(x, y, w, h, stroke=1, fill=0)
            # upper left x,y and lower right x,y of bounding rectangle
            c.arc(x - w, y, x + w, y + h, startAng = 270, extent = 180)
            # line closing the arc
            c.line(x, y, x, y + h)

        finally:
            c.restoreState()

        return

    def __drawFace(self, c, x, y, w, h):
        """
            draw face bounding rectangle
        """
        c.saveState()
        try:
            # # overall bounding rectangle
            # c.setStrokeColorRGB(200/255, 50/255, 120/255)
            # c.rect(x, y, w, h, stroke=1, fill=0)

            # # bottom bounding rectangle
            # c.setStrokeColorRGB(40/255, 225/255, 40/255)
            hBot = h * 0.8526
            wBot = -1.0 * h * 0.077
            yBot = y + ((h / 2.0) - (hBot / 2.0))
            # c.rect(x, yBot, wBot, hBot, stroke=1, fill=0)

            # bottom arc
            c.setStrokeColorRGB(50/255, 50/255, 255/255)
            c.arc(x, yBot, x + (wBot * 2.0), yBot + hBot, startAng = 90, extent = 180)

            # # top bounding rectangle
            # c.setStrokeColorRGB(40/255, 225/255, 40/255)
            hTop = h
            wTop = -1.0 * h * 0.0385
            # c.rect(x + w - wTop, y, wTop, hTop, stroke=1, fill=0)

            # top arc
            c.setStrokeColorRGB(50/255, 50/255, 255/255)
            c.arc(x + w - wTop, y, (x + w - wTop) + (wTop * 2.0), y + hTop, startAng = 90, extent = 180)

            # draw lines between arcs
            c.line(x + wBot, yBot, x + w, y)
            c.line(x + wBot, yBot + hBot, x + w, y + h)

        finally:
            c.restoreState()

        return

    def __drawNose(self, c, x, y, w, h):
        """
            draw nose bounding rectangle
        """

        # drawLabel(c, x + (0.2 * cm), y + (h / 2.0), "seam allowance - BOTTOM")

        gapLength = w * (1.0 - 0.773)
        c.saveState()
        try:
            # # draw bounding rectangle
            # c.setStrokeColorRGB(200/255, 50/255, 120/255)
            # c.rect(x, y, w, h, stroke=1, fill=0)

            # draw arc
            c.setStrokeColorRGB(50/255, 50/255, 255/255)
            # c.rect(x, y, w, h, stroke=1, fill=0)
            # upper left x,y and lower right x,y of bounding rectangle
            c.arc(x, y, x + (2.0 * w), y + h, startAng = 90, extent = 180)
            # wing shape under eyes
            c.line(x + w, y, x + w - gapLength, y + (h / 2.0))
            c.line(x + w - gapLength, y + (h / 2.0), x + w, y + h)

        finally:
            c.restoreState()

        return

    def maskPrint(self, chinToNeck, jawBones, noseLength):
        """
            document upper left is (0,0), x increments are positive, y increments are negative
        """
        cmH = 28 * cm
        cmW = 21 * cm
        cmMargin = 2.0 * cm  # just selected 1.0 cm margins on the width edges, some printers truncate this area

        # canv = canvas.Canvas(PDFPathFn, pagesize=(cmW, cmH))  # this creates a hard file ....
        self.imgBuffer.seek(0)
        canv = canvas.Canvas(self.imgBuffer, pagesize=(cmW, cmH))
        canv.translate(0, 28 * cm) # set the top of the page as the origin (i.e. upper left is 0,0)
        # canv.saveState()
        # drawLabel(canv, 5 * cm, -5 * cm, "TOP")
        # canv.restoreState()

        self.__drawGrid(canv)  # lay down a 1x1 cm grid

        # determine overall width of shapes
        faceTopW = jawBones * cm * 0.0385
        faceMidW = jawBones * cm * 0.2436
        faceBotW = jawBones * cm * 0.0770

        faceW = faceTopW + faceMidW + faceBotW
        chinW = chinToNeck * cm
        noseW = noseLength / 0.773 * cm

        shapeW = chinW + faceW + noseW
        betweenShapesW = (cmW - shapeW - cmMargin) / 2.0

        chinTopX = (cmMargin / 2.0)
        faceTopX = chinTopX + chinW + betweenShapesW
        noseTopX = faceTopX + faceW + betweenShapesW

        # center shapes on documents, increases in y are negative values
        chinTopY = -1 * cmH / 2.0 + (jawBones * cm * 0.69 / 2.0)
        faceTopY = -1 * cmH / 2.0 + (jawBones * cm / 2.0)
        noseTopY = -1 * cmH / 2.0 + (jawBones * cm * 0.77 / 2.0)

        # print("chinStart(x,y): {},{}".format(chinTopX, chinTopY))
        # print("faceStart(x,y): {},{}".format(faceTopX, faceTopY))
        # print("noseStart(x,y): {},{}".format(noseTopX, noseTopY))

        # render the 3 objects on the page from left to right
        self.__drawChin(canv, chinTopX, chinTopY, chinW, (-1 * jawBones * cm * 0.69))
        self.__drawFace(canv, faceTopX, faceTopY, faceW, (-1 * jawBones * cm))
        self.__drawNose(canv, noseTopX, noseTopY, noseW, (-1 * jawBones * cm * 0.77))

        canv.save()
        self.imgBuffer.seek(0)
        response = cloudinary.uploader.upload(self.imgBuffer)

        return response["url"]


if __name__ == '__main__':
    print("Hello from module %s. Python version: %s" % (sys.argv[0], sys.version))
    sys.stdout.write("--------------------------------------------------------------\n")
    sys.stdout.write("Start of %s Job: %s\n\n" % (sys.argv[0], time.strftime("%H:%M:%S", time.localtime())))

    obj = MaskPatternPrint()
    # args to maskPrint: chinToNeck, jawBones, noseLength in cm, Brad's approx measurements follow
    url = obj.maskPrint(4.0, 22.7, 5.0)  # args: 3.6, 15.6, 3.4 measured from the pattern in https://singer.com.hk/blogs/sewing-projects/how-to-make-face-mask
    print("url of Mask Pattern PDF:{}".format(url))

    del obj

    sys.stdout.write("\n\nEnd of %s Job: %s\n" % ( \
    sys.argv[0], time.strftime("%H:%M:%S", time.localtime())))
    sys.stdout.write("-------------------------------------------------------------\n")