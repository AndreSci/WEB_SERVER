import logging


def block_flask_logs():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
