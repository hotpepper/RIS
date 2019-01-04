import psycopg2
import pyodbc
import getpass
import time
import pandas as pd
from collections import defaultdict, namedtuple
import sys
import copy_schema_between_pg_databases as pg_io
import pg_import_export_shps as pg_shp

def timeDec(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print '%r %2.2f sec' % (method.__name__, te - ts)
        return result
    return timed


class PostgresDb(object):
    """
    Database connection helper fucntion for PostgreSQL
     :host param: server path
     :db_name param: database name
     :user kwarg: username
     :db_pass kwarg: password
     :quiet kwarg: turns off print statments, useful for multiple writes
    """
    def __init__(self, host, db_name, **kwargs):  # user=None, db_pass=None):
        self.quiet = kwargs.get('quiet', False)
        self.params = {
            'dbname': db_name,
            'user': kwargs.get('user', None),
            'password': kwargs.get('db_pass', None),
            'host': host,
            'port': 5432
        }
        if not kwargs.get('db_pass', None):
            self.db_login()
        self.conn = psycopg2.connect(**self.params)

    def db_login(self):
        if not self.params['user']:
            self.params['user'] = raw_input('User name ({}):'.format(
                self.params['dbname'])).lower()
        self.params['password'] = getpass.getpass('Password ({})'.format(
            self.params['dbname']))

    def dbConnect(self):
        self.conn = psycopg2.connect(**self.params)

    def dbClose(self):
        self.conn.close()

    def query(self, qry):
        output = namedtuple('output', 'data, columns, desc')
        cur = self.conn.cursor()
        qry = qry.replace('%', '%%')
        qry = qry.replace('-pct-', '%')
        try:
            cur.execute(qry)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                desc = cur.description
                data = cur.fetchall()
            else:
                data = None
                desc = None
                columns = None
                self.conn.commit()
                if not self.quiet:
                    print 'Update sucessfull'
            del cur
            if columns:
                return output(data=data, columns=columns, desc=desc)
            else:
                return output(data=data, columns=None, desc=None)
        except:
            print 'Query Failed:\n'
            for i in qry.split('\n'):
                print '\t{0}'.format(i)
            self.conn.rollback()
            del cur
            sys.exit()


    def import_table(self, table_name, csv, seperator=','):
        cur = self.conn.cursor()
        with open(csv) as f:
            cur.copy_from(f, table_name, sep=seperator, null='')
        print '{} imported to {}'.format(csv, table_name)
        self.conn.commit()

    def export_table(self, table_name, csv, seperator=','):
        cur = self.conn.cursor()
        with open(csv) as f:
            cur.copy_to(f, table_name, sep=seperator, null='')
        print '{} exported to {}'.format(csv, table_name)


class SqlDb(object):
    """
        Database connection helper fucntion for MS SQL server
         :db_server param: server path
         :db_name param: database name
         :user kwarg: username
         :db_pass kwarg: password
         :quiet kwarg: turns off print statments, useful for multiple writes
        """
    def __init__(self, db_server, db_name, **kwargs):  # user=None, db_pass=None):
        self.quiet = kwargs.get('quiet', False)
        self.params = {
            'DRIVER': 'SQL Server', #'SQL Server Native Client 10.0',
            'DATABASE': db_name,
            'UID': kwargs.get('user', None),
            'PWD': kwargs.get('db_pass', None),
            'SERVER': db_server
        }
        if not kwargs.get('db_pass', None):
            self.db_login()
        self.dbConnect()

    def db_login(self):
        """
        if login info has not been passed, get credentials
        :return:
        """
        if not self.params['UID']:
            self.params['UID'] = raw_input('User name ({}):'.format(
                self.params['DATABASE']))
        self.params['PWD'] = getpass.getpass('Password ({})'.format(
            self.params['DATABASE']))
        # will echo in idle, push pass off screen
        print '\n'*1000

    def dbConnect(self):
        self.conn = pyodbc.connect(**self.params)

    def dbClose(self):
        self.conn.close()

    def query(self, qry):
        output = namedtuple('output', 'data, columns, desc')
        cur = self.conn.cursor()
        qry = qry.replace('%', '%%')
        qry = qry.replace('-pct-', '%')
        try:
            # TODO: fix this band aide solution - nateive client is required to appropriately handle datetime2 types
            # reconnect with native driver for desc (datetime2)
            del cur
            self.params['DRIVER'] = 'SQL Server Native Client 10.0'
            self.dbConnect()
            cur = self.conn.cursor()
            cur.execute(qry)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                desc = cur.description
                # TODO: fix this band aide solution - SQL server driver is required to appropriately handle byte arrays
                # reconnect with old driver for data
                self.params['DRIVER'] = 'SQL Server'
                self.dbConnect()
                del cur
                cur = self.conn.cursor()
                cur.execute(qry)
                data = cur.fetchall()
            else:
                data = None
                columns = None
                desc = None
                self.conn.commit()
                if not self.quiet:
                    print 'Update sucessfull'
            del cur
            if columns:
                return output(data=data, columns=columns, desc=desc)
                # return output(data=data, columns=columns)
            else:
                return output(data=data, columns=None, desc=None)
        except:
            print 'Query Failed:\n'
            for i in qry.split('\n'):
                print '\t{0}'.format(i)
            self.conn.rollback()
            del cur
            sys.exit()


def data_to_dict_data(data, columns):
    dictdata = defaultdict(list)
    for row in data:
        # loop through columns to get index
        for c in range(len(columns)):
            # add row's value by index to dict
            dictdata[columns[c]].append(row[c])
    return dictdata


def query_to_table(db, qry):
    data, col = db.query(qry)  # run query
    dd = data_to_dict_data(data, col)  # convert to dictionary
    df = pd.DataFrame(dd, columns=col)  # convert to pandas dataframe
    return df


def copy_table():
    pg_io.connection_ui(PostgresDb)