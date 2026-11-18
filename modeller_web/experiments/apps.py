from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _configure_sqlite_concurrency(sender, connection, **kwargs):
    """Ativa modo WAL e busy_timeout no SQLite para suportar múltiplos acessos simultâneos."""
    if connection.vendor == 'sqlite':
        db_name = str(connection.settings_dict.get('NAME', ''))
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA busy_timeout = 30000;')
            if db_name and ':memory:' not in db_name:
                cursor.execute('PRAGMA journal_mode = WAL;')
                cursor.execute('PRAGMA synchronous = NORMAL;')


class ExperimentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'experiments'

    def ready(self):
        connection_created.connect(_configure_sqlite_concurrency)
