from ris import csvIO
from ris.db2 import pg_io
import decimal
import datetime
import os


def get_table_fromsql_query(sql, qry):
    # assumes full query including schema etc passed
    q = sql.query("""select top 1 * from ({q}) as q""".format(q=qry))
    path = os.path.join(os.getcwd(), 'data.csv')

    cmd = """sqlcmd -S {serv} -d {db} -U {usr} -P {pas} 
        -Q "set nocount on; select * from ({q}) as q" 
        -o {p} -h-1 -s "|" -W """.format(db=sql.params['DATABASE'],
                                         serv=sql.params['SERVER'],
                                         pas=sql.params['PWD'],
                                         usr=sql.params['UID'],
                                         q=qry,
                                         p=path)
    os.system(cmd.replace('\n', ' '))
    clean_output(path)
    return q._replace(data=None)


def get_table_from_sql(sql, sql_schema, sql_table):
    # TODO: add option to pass in query instead of full table
    q = sql.query("""select top 1 * from {db}.{sch}.{tbl}""".format(db=sql.params['DATABASE'],
                                                                    sch=sql_schema,
                                                                    tbl=sql_table))
    path = os.path.join(os.getcwd(), 'data.csv')

    cmd = """sqlcmd -S {serv} -d {db} -U {usr} -P {pas} 
    -Q "set nocount on; select * from {db}.{sch}.{tbl}" 
    -o {p} -h-1 -s "|" -W """.format(db=sql.params['DATABASE'],
                                     serv=sql.params['SERVER'],
                                     pas=sql.params['PWD'],
                                     usr=sql.params['UID'],
                                     sch=sql_schema,
                                     tbl=sql_table,
                                     p=path)
    os.system(cmd.replace('\n', ' '))
    clean_output(path)
    return q._replace(data=None)


def clean_output(path):
    # TODO: remove this, and fix work around or allow for batching (for large files)
    # needed for copy_from to deal with escape characters correctly - band aid that should be revisited
    in_data = csvIO.read(path)
    out_data = list()
    for row in in_data:
        out_data.append([i.replace('\\', '\\\\') for i in row])
    os.remove(path)
    csvIO.write(path, out_data)


def add_table_to_pgsql(pg, pg_schema, pg_table, table_data, archive=False, permission_default=False):
    if archive:
        exists = pg.query("""SELECT EXISTS (
                            SELECT 1
                            FROM   information_schema.tables
                            WHERE  table_schema = '{s}'
                            AND    table_name = '{t}'
                           );""".format(t=pg_table, s=pg_schema))
        if exists.data[0][0]:
            pg.query("drop table if exists archive.{}".format(pg_table))
            pg.query("create table archive.{t} as select * from {s}.{t}".format(t=pg_table, s=pg_schema))
            pg.query("alter table archive.{t} add archived_dte timestamp".format(
                t=pg_table, s=pg_schema))
            pg.query("update archive.{t} set archived_dte=now()".format(t=pg_table, s=pg_schema))
        else:
            print 'No existing table to archive'

    pg.query("drop table if exists {s}.{t}".format(t=pg_table, s=pg_schema))
    pg.query(build_table(pg_schema, pg_table, table_data))
    path = os.path.join(os.getcwd(), 'data.csv')
    pg_io.add_data_to_pg(pg, pg_table, pg_schema, '|', path, 'NULL')
    if not permission_default:
        if raw_input('Grant permissions to public (Y/N)?\n').upper() == 'Y':
            pg.query('GRANT ALL ON {}.{} TO PUBLIC;'.format(pg_schema, pg_table))
    else:
        pg.query('GRANT ALL ON {}.{} TO PUBLIC;'.format(pg_schema, pg_table))

    q = pg.query("Select count(*) from {}.{}".format(pg_schema, pg_table))
    print 'Added {} rows to {}.{}'.format(int(q.data[0][0]), pg_schema, pg_table)


def parse_row(row):
    name, typ, disp, intsz, persc, scl, nul = row
    if typ in (str, unicode):
        return "{n} varchar({s})".format(n=name, s=persc)
    elif typ == bytearray:
        return "{n} bytea".format(n=name)
    elif typ in (decimal.Decimal, int, float, long):
        return "{n} numeric".format(n=name)
    elif typ == datetime.datetime:
        return "{n} timestamp".format(n=name)
    elif typ == datetime.date:
        return "{n} date".format(n=name)



def build_table(pg_schema, pg_table, table_data):
    qry = "create table {s}.{t} (".format(s=pg_schema, t=pg_table)
    for row in table_data.desc:
        qry += "\n\t{},".format(parse_row(row))
    qry = qry[:-1] + ")"
    return qry


def connection_ui(sql=None, pg=None):
    q = raw_input('Get data from full table (T) or query (Q)\n').upper()

    if not sql:  # passed in sql connection
        org_server = raw_input('\nOrigin SQL server name:\n')
        org_db = raw_input('\nOrigin SQL databse name:\n')
        org_user = raw_input('\nOrigin db login user name:\n')
        sql = db2.SqlDb(org_server, org_db, user=org_user, quiet=True)
    else:
        org_server = sql.params['SERVER']
        org_db = sql.params['DATABASE']
    if q == 'T':
        org_schema = raw_input('\nOrigin SQL schema name:\n')
        org_table = raw_input('\nOrigin SQL table name:\n')

    if not pg:  # passed in sql connection
        dest_server = raw_input('\nDestination PG server name:\n')
        dest_db = raw_input('\nDestination PG databse name:\n')
        dest_user = raw_input('\nDestination db login user name:\n')
        pg = db2.PostgresDb(dest_server, dest_db, user=dest_user, quiet=True)
    else:
        dest_server = pg.params['host']
        dest_db = pg.params['dbname']
        dest_user = pg.params['user']

    dest_schema = raw_input('\nDestination PG schema name:\n')

    if q == 'T':
        if raw_input('\nRename table? (Y/N)\n').lower() == 'y':
            dest_table = raw_input('Destination table name:\n')
        else:
            dest_table = org_table
        table = get_table_from_sql(sql, org_schema, org_table)
    else:
        dest_table = raw_input('\nNew table name:\n').lower()
        qry = raw_input('QUERY =:\n')
        table = get_table_fromsql_query(sql, qry)

    add_table_to_pgsql(pg, dest_schema, dest_table, table, True, True)


if __name__ == '__main__':
    connection_ui()
