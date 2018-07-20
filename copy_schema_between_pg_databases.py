# from db2 import PostgresDb
import os

def copy_schema_between_pg_databases(pg_org, pg_dest, table_name, table_schema, dest_schema=None, dest_table_name=None):
    if not dest_schema:
        dest_schema = 'public'
    if not dest_table_name:
        dest_table_name = table_name
    # get schema of table in org loc
    schema = pg_org.query("""
                            select column_name, data_type, character_maximum_length
                            from INFORMATION_SCHEMA.COLUMNS 
                            where table_name = '{}' and table_schema = '{}';
                        """.format(table_name, table_schema))
    # make sure doesnt exist
    if not dest_schema:
        dest_schema = 'public'
    if not dest_table_name:
        dest_table_name = table_name
    pg_dest.query("Drop table if exists {}.{}".format(dest_schema, dest_table_name), True)
    # add 1st column
    pg_dest.query("Create table {}.{} ({} {})".format(dest_schema, dest_table_name, schema.data[0][0], schema.data[0][1]), True)
    # add the rest of the columns
    for (c, t, l) in schema.data[1:]:
        if c == 'geom':
            geo_type = pg_org.query("""SELECT type 
                                        FROM geometry_columns 
                                        WHERE f_table_name = '{}' and f_table_schema = '{}'
                                        and f_geometry_column = 'geom';""".format(table_name, table_schema))
            t = 'geometry({},2263)'.format(geo_type.data[0][0])
        pg_dest.query("alter table {}.{} add  column {} {}".format(dest_schema, dest_table_name, c, t), True)
        if c == 'geom':
            print 'Indexing geometry field\n'
            pg_dest.query("CREATE INDEX {tbl}_gist ON {tbl} USING gist (geom);".format(tbl=dest_table_name))

    print 'Table {} is done'.format(dest_table_name)

    
def export_data_from_pg(pg, table_schema, table_name, seperator='|'):
    """
    assumes tables exist with correct schema
    :return:
    """
    cur = pg.conn.cursor()
    with open('temp_table.csv', 'wb') as f:
        cur.copy_to(f, '{}.{}'.format(table_schema, table_name), sep=seperator, null='')

        
def add_data_to_pg(pg, dest_table_name, dest_schema=None, seperator='|', tbl='temp_table.csv'):
    """
    assumes tables exist with correct schema
    :return:
    """
    loc_table = dest_schema.lower()+'.'+dest_table_name.lower()
    cur = pg.conn.cursor()
    with open(tbl) as f:
        cur.copy_from(f, loc_table, sep=seperator, null='')
    pg.conn.commit()
    os.remove(os.path.join(os.getcwd(), tbl))  # clean up after yourself in the folder


def copy_data_between_pg_databases(pg_org, pg_dest, table_name, table_schema, dest_schema=None, dest_table_name=None):
    if not dest_schema:
        dest_schema = 'public'
    if not dest_table_name:
        dest_table_name = table_name
    export_data_from_pg(pg_org, table_schema, table_name, '|')
    add_data_to_pg(pg_dest, dest_table_name, dest_schema, '|')
    if raw_input('Grant permissions to public (Y/N)?\n').upper() == 'Y':
        pg_dest.query('GRANT ALL ON {}.{} TO PUBLIC;'.format(dest_schema, dest_table_name))
    print 'Transfered data from {} {} to {} {}'.format(pg_org.params['dbname'], table_name, pg_dest.params['dbname'], dest_table_name)


def defaults(schema):
    if not schema:
        return 'public'
    else:
        return schema


def run_full_copy(pg_orgin, pg_destination, org_schema, dest_schema, org_table, dest_table=None):
    """
        inputs origin: database connect, schema, table name; destination: database connect, schema, table name
        copies table schema from origin to desintation
        copies data from origin to destination 
    """
    org_schema = defaults(org_schema)
    dest_schema = defaults(dest_schema)
    if not dest_table:
        dest_table = org_table
    copy_schema_between_pg_databases(pg_orgin, pg_destination, org_table, org_schema, dest_schema, dest_table)
    copy_data_between_pg_databases(pg_orgin, pg_destination, org_table, org_schema, dest_schema, dest_table)
    

def connection_ui():
    org_server = raw_input('\nOrigin server name:\n')
    org_db = raw_input('\nOrigin databse name:\n')
    org_user = raw_input('\nOrigin db login user name:\n')
    pg_org = PostgresDb(org_server, org_db, org_user)
    org_schema = raw_input('\nOrigin schema name:\n')
    org_table = raw_input('\nOrigin table name:\n')

    dest_server = raw_input("\nDestination server name (type 'same' to reuse server from origin):\n")
    if dest_server.lower() == 'same':
        dest_server = org_server
    dest_db = raw_input("\nDestination databse name (type 'same' to reuse database from origin):\n")
    if dest_db.lower() == 'same':
        dest_db = org_db
    dest_pass = None
    dest_user = raw_input("\nDestination db login user name (type 'same' to reuse user name from origin):\n")
    if dest_user.lower() == 'same':
        dest_user = org_user
        dest_pass = pg_org.params['password']
    pg_dest = PostgresDb(dest_server, dest_db, dest_user, dest_pass)
    dest_schema = raw_input("\nDestination schema name (type 'same' to reuse schema from origin):\n")
    if dest_schema.lower() == 'same':
        dest_schema = org_schema
    if raw_input('\nRename table? (Y/N)\n').lower() == 'y':
        dest_table = raw_input('Destination table name:\n')
    else:
        dest_table = org_table
    run_full_copy(pg_org, pg_dest, org_schema, dest_schema, org_table, dest_table)
    while raw_input('Copy another table between the same databases? (Y/N)\n').upper() == 'Y':
        org_table = raw_input('\nOrigin table name:\n')
        run_full_copy(pg_org, pg_dest, org_schema, dest_schema, org_table)
    print 'Done\n'
        
    

    
if __name__ == '__main__':
    connection_ui()

