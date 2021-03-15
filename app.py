"""
    App entry point
"""
from flask import Flask, request
from mask2care import Mask2Care

app = Flask(__name__)
appClass = Mask2Care()

@app.route('/orderoptions', methods=['GET'])
def getOrderOptions():
    if request.method == 'GET':
        item = request.args.get('selfie', default=None, type=str)  # items is intended to be a comma delimited string

        return appClass.getOrderOptions(item)

    return

if __name__ == '__main__':
    app.run()
