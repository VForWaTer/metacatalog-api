import os

from metacatalog_api import core


def migrate(schema: str = 'public'):
    """
    Migrate the database schema to the latest version.
    :param schema: The schema holding the tables, usually 'public' (default)
    """
    core.migrate_db(schema=schema)


if __name__ == '__main__':
    import fire
    fire.Fire(migrate)
    