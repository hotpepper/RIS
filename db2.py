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
    def __init__(self, host, db_name, user=None, db_pass=None):
        self.quiet = raw_input('Quiet mode on <Y/N>?\n').upper()
        if self.quiet == 'Y':
            self.quiet = True
        else:
            quiet = False
        self.params = {
            'dbname': db_name,
            'user': user,
            'password': db_pass,
            'host': host,
            'port': 5432
        }
        if not db_pass:
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
        output = namedtuple('output', 'data, columns')
        cur = self.conn.cursor()
        qry = qry.replace('%', '%%')
        qry = qry.replace('-pct-', '%')
        try:
            cur.execute(qry)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
            else:
                data = None
                columns = None
                self.conn.commit()
                if not self.quiet:
                    print 'Update sucessfull'
            del cur
            if columns:
                return output(data=data, columns=columns)
            else:
                return output(data=data, columns=None)
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
    def __init__(self, db_server, db_name, user=None, db_pass=None):
        self.quiet = raw_input('Quiet mode on <Y/N>?\n').upper()
        if self.quiet == 'Y':
            self.quiet = True
        else:
            quiet = False
        self.params = {
            'DRIVER': 'SQL Server',
            'DATABASE': db_name,
            'UID': user,#raw_input('User name (SQL):'),
            'PWD': db_pass,#getpass.getpass('Password (SQL)'),
            'SERVER': db_server
        }
        if not db_pass:
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
        output = namedtuple('output', 'data, columns')
        cur = self.conn.cursor()
        qry = qry.replace('%', '%%')
        qry = qry.replace('-pct-', '%')
        try:
            cur.execute(qry)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
            else:
                data = None
                columns = None
                self.conn.commit()
                if not self.quiet:
                    print 'Update sucessfull'
            del cur
            if columns:
                return output(data=data, columns=columns)
            else:
                return output(data=data, columns=None)
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

