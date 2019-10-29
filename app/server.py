from loguru import logger
from . import create_app

app = create_app()

if __name__ == '__main__':
    logger.debug(f'Starting Flask app')

    from .routes import socketio
    assert(socketio is not None)
    socketio.run(app)
