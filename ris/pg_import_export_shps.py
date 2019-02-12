import os
import subprocess
import getpass
import datetime
import ris




def export_pg_table_to_shp(export_path, pgo, pgtable_name, **kwargs):  # kwargs: pgschema, pg_sql_select, shp_name
    """
        source: https://gist.github.com/justinlewis/4398913
    """
    pgschema = kwargs.get('pgschema', 'public')
    pg_sql_select = 'select * from {}.{}'.format(pgschema, pgtable_name)
    shp_name = kwargs.get('shp_name', pgtable_name)
    # if not pgschema:
    #     pgschema = 'public'
    # if not pg_sql_select:
    #     pg_sql_select = 'select * from {}.{}'.format(pgschema, pgtable_name)

    cmd = 'ogr2ogr -overwrite -f \"ESRI Shapefile\" \"{export_path}\{shpname}.shp\" ' \
          'PG:"host={host} user={username} dbname={db} ' \
          'password={password}" -sql "{pg_sql_select}"'.format(pgtable_name=pgtable_name,
                                                               export_path=export_path,
                                                               shpname=shp_name,
                                                               host=pgo.params['host'],
                                                               username=pgo.params['user'],
                                                               db=pgo.params['dbname'],
                                                               password=pgo.params['password'],
                                                               pg_sql_select=pg_sql_select)
    print 'ogr2ogr -overwrite -f \"ESRI Shapefile\" \"{export_path}\{shpname}.shp\" ' \
          'PG:"host={host} user={username} dbname={db} ' \
          'password={password}" -sql "{pg_sql_select}"'.format(pgtable_name=pgtable_name,
                                                               export_path=export_path,
                                                               shpname=shp_name,
                                                               host=pgo.params['host'],
                                                               username=pgo.params['user'],
                                                               db=pgo.params['dbname'],
                                                               password='*'*len(pgo.params['password']),
                                                               pg_sql_select=pg_sql_select)
    os.system(cmd)
    print 'Done!'


def get_geom_column(dbo, schema, table):
    d = dbo.query('select * from {s}."{t}" limit 0'.format(s=schema, t=table))
    geo = None
    for row in d.desc:
        if row.type_code == 26840:
            geo = row.name
    return geo


def import_shp_to_pg(import_shp, pgo, schema='public', precision=False, permission=True,
                     gdal_data=r"C:\Program Files (x86)\GDAL\gdal-data"):
    import_shp = import_shp.lower()
    if precision:
        precision = '-lco precision=NO'
    else:
        precision = ''
    cmd = 'ogr2ogr --config GDAL_DATA "{gdal_data}" -nlt PROMOTE_TO_MULTI -overwrite -a_srs ' \
          'EPSG:{srid} -progress -f "PostgreSQL" PG:"host={host} port=5432 dbname={dbname} ' \
          'user={user} password={password}" "{shp}" -nln {schema}.{tbl_name} {perc} '.format(
            gdal_data=gdal_data,
            srid='2263',
            host=pgo.params['host'],
            dbname=pgo.params['dbname'],
            user=pgo.params['user'],
            password=pgo.params['password'],
            shp=import_shp,
            schema=schema,
            tbl_name=os.path.basename(import_shp).replace('.shp',''),
            perc=precision
            )
    subprocess.call(cmd, shell=True)
    q = """comment on table {s}."{t}" is '{t} created by {u} on {d}  - imported using ris module vesion {v}'""".format(
                    s=schema,
                    t=os.path.basename(import_shp).replace('.shp','').lower(),
                    u=getpass.getuser(),
                    d=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                    v=ris.__version__
                )
    pgo.query(q)
    print 'Indexing...'
    geo = get_geom_column(pgo, schema, os.path.basename(import_shp).replace('.shp', ''))
    pgo.query('CREATE INDEX "{t}_geom_gist" ON {s}."{t}" USING gist ({g});'.format(
        t=os.path.basename(import_shp).replace('.shp', ''),
        s=schema,
        g=geo
    ))
    if permission:
        pgo.query('grant all on {s}."{t}" to public;'.format(
            s=schema, t=os.path.basename(import_shp).replace('.shp', '')))


def import_from_gdb_to_pg(gdb, feature, pgo, schema='public', permission=True,
                          gdal_data=r"C:\Program Files (x86)\GDAL\gdal-data"):
    cmd = 'ogr2ogr --config GDAL_DATA "{gdal_data}" -nlt PROMOTE_TO_MULTI -overwrite -a_srs ' \
          'EPSG:{srid} -f "PostgreSQL" PG:"host={host} user={user} dbname={dbname} ' \
          'password={password}" "{gdb}" "{feature}" -nln {sch}.{feature} -progress'.format(gdal_data=gdal_data,
                                                            srid='2263',
                                                            host=pgo.params['host'],
                                                            dbname=pgo.params['dbname'],
                                                            user=pgo.params['user'],
                                                            password=pgo.params['password'],
                                                            gdb=gdb,
                                                            feature=feature,
                                                            sch=schema
                                                            )
    subprocess.call(cmd, shell=True)
    q = """comment on table {s}."{t}" is '{t} created by {u} on {d} - imported using ris module vesion {v}'""".format(
        s=schema,
        t=feature,
        u=getpass.getuser(),
        d=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        v=ris.__version__
    )
    pgo.query(q)
    print 'Indexing...'
    geo = get_geom_column(pgo, schema, feature)
    pgo.query('CREATE INDEX "{t}_geom_gist" ON {s}."{t}" USING gist ({g});'.format(
        t=feature,
        s=schema,
        g=geo
    ))
    if permission:
        pgo.query('grant all on {s}."{t}" to public;'.format(
            s=schema, t=feature))
