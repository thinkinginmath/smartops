import logging

from smartops.api import app
from smartops.utils import flags
from smartops.utils import logsetting


flags.add('server_host',
          help='server host address',
          default='0.0.0.0')
flags.add_bool('debug',
               help='run in debug mode',
               default=True)


if __name__ == '__main__':
    flags.init()
    logsetting.init()
    logging.info('run server')
    app.run(host=flags.OPTIONS.server_host, port=8000, debug=flags.OPTIONS.debug)
