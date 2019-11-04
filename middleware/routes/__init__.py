from flask_socketio import SocketIO
from loguru import logger

socketio = None


def init_app(app):
    from . import files, ping

    global socketio

    logger.debug('Opening websocket')
    socketio = SocketIO(app, cors_allowed_origins="*")

    logger.debug('Registering ping api')
    ping.register_as_plugin(app)

    logger.debug('Registering file api')
    files.register_as_plugin(app)
