from captcha import CaptchaSovler

from flask import Flask
from flask import request
from werkzeug import secure_filename


app = Flask(__name__)

@app.route('/solve', methods=['GET', 'POST'])
def solve():
    if request.method == 'POST':
        try:
            file = request.files['captcha_image']
            return CaptchaSovler.solve_image(file.read())
        except:
            return ''

if __name__ == '__main__':
    app.run()

# aa = _solve_image('/tmp/95.jpg')
# print(aa)
