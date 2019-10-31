from flask_socketio import SocketIO
from loguru import logger

socketio = None


def init_app(app):
    global socketio

    logger.debug('Opening websocket')
    socketio = SocketIO(app, cors_allowed_origins="*")

    from .files import register_as_plugin

    logger.debug('Registering file api')
    register_as_plugin(app)
