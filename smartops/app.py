from flask import Blueprint
from flask import Flask
from flask_cors import CORS
from flask_principal import Principal

from smartops.api.api import api
from smartops.utils import setting_wrapper

principals = Principal()
def create_app():
    app = Flask(__name__)
    app.debug = True
    return app

app = create_app()
CORS(app)
app.register_blueprint(api)


if __name__ == '__main__':
    app.run(port=8000, threaded=True)
