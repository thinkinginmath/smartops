"""utility binary to manage database."""
import os
import os.path
import sys


current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_dir)


from flask.ext.script import Manager

from smartops import app
from smartops.db.handlers import database
from smartops.utils import flags
from smartops.utils import logsetting
from smartops.utils import setting_wrapper as setting


flags.add('table_name',
          help='table name',
          default='')
flags.add('apps',
          help=(),
          default='')

flags.add('search_app_properties',
          help='comma separated properties to search in app config',
          default='')

app_manager = Manager(app.create_app(), usage="Perform database operations")


TABLE_MAPPING = {
}


@app_manager.command
def list_config():
    "List the commands."
    for key, value in app.config.items():
        print key, value


@app_manager.command
def checkdb():
    """check if db exists."""
    if setting.DATABASE_TYPE == 'file':
        if os.path.exists(setting.DATABASE_FILE):
            sys.exit(0)
        else:
            sys.exit(1)

    sys.exit(0)


@app_manager.command
def createdb():
    """Creates database from sqlalchemy models."""
    database.init()
    try:
        database.drop_db()
    except Exception:
        pass

    if setting.DATABASE_TYPE == 'file':
        if os.path.exists(setting.DATABASE_FILE):
            os.remove(setting.DATABASE_FILE)
    database.create_db()
    if setting.DATABASE_TYPE == 'file':
        os.chmod(setting.DATABASE_FILE, 0o777)


@app_manager.command
def dropdb():
    """Drops database from sqlalchemy models."""
    database.init()
    database.drop_db()


if __name__ == "__main__":
    flags.init()
    logsetting.init()
    app_manager.run()
