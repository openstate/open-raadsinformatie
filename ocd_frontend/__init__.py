from flask import Flask

app = Flask(__name__)
app.config['USE_X_SENDFILE'] = True

from . import routes
