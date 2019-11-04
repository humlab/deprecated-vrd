from flask import Blueprint
from flask_restful import Api, Resource


ping_blueprint = Blueprint("ping", __name__)
ping_api = Api(ping_blueprint)


class Ping(Resource):
    def get(self):
        return {"status": "success", "message": "pong"}


ping_api.add_resource(Ping, "/ping")


def register_as_plugin(app):
    app.register_blueprint(ping_blueprint)
