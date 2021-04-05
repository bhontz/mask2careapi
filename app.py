"""
    App entry point
"""
from flask import Flask, request
from mask2care import Mask2Care

app = Flask(__name__)
appClass = Mask2Care()

@app.route('/')
def sayHello():
        return 'www.pinpointview.com is under construction, thank you for visiting'

@app.route('/orderoptions', methods=['GET'])
def getOrderOptions():
    if request.method == 'GET':
        item = request.args.get('selfie', default=None, type=str)  # item is intended to be an image URL

        return appClass.getOrderOptions(item)

    return

@app.route('/maskpattern', methods=['GET'])
def getMaskPattern():
    if request.method == 'GET':
        item = request.args.get('selfie', default=None, type=str)  # item is intended to be an image URL

        return appClass.getMaskPattern(item)

    return


if __name__ == '__main__':
    app.run()
