def init_app(app):
    from . import files, ping, fingerprint

    files.register_as_plugin(app)

    ping.register_as_plugin(app)

    fingerprint.register_as_plugin(app)
