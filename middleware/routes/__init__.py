def init_app(app):
    from . import files, ping

    files.open_websocket(app)
    files.register_as_plugin(app)

    ping.register_as_plugin(app)
