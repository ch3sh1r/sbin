#!/usr/bin/env python3
import logging
from sqlite3 import IntegrityError

from web import DB

MAX_MIGRATION_ID = 1


def get_tables(db):
    res = db.execute('''
        SELECT name FROM sqlite_master WHERE type='table'
    ''')
    return [x[0] for x in res.fetchall()]


def get_migration_id(db):
    if 'config' not in get_tables(db):
        return 0
    res = db.execute('''
        SELECT value FROM config
        WHERE id = 'migration_id'
    ''')
    return int(res.fetchone()[0])


def set_migration_id(db, mid):
    try:
        db.execute('''
            INSERT INTO config (id, value)
            VALUES ('migration_id', '%d')
        ''' % mid)
        db.commit()
    except IntegrityError:
        db.execute('''
            UPDATE config SET value = '%d'
            WHERE id = 'migration_id'
        ''' % mid)
        db.commit()


def step1(db):
    db.execute('''
        CREATE TABLE config (
            id TEXT(20) PRIMARY KEY,
            value TEXT
        ) WITHOUT ROWID
    ''')
    db.execute('''
        CREATE TABLE dump (
            id INTEGER(8) PRIMARY KEY,
            data BLOB
        ) WITHOUT ROWID
    ''')


def main():
    logging.info('Start migration')
    for mid in range(get_migration_id(DB) + 1, MAX_MIGRATION_ID + 1):
        logging.info('Running migration#%d' % mid)
        globals()['step%d' % mid](DB)
        set_migration_id(DB, mid)
    logging.info('Done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
