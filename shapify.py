import arcpy
import datetime
import os
import getpass
SREFERENCE = r'\\Dot55fp05\botplan\RIS\Data\Streets\LION\LION_Wild\17D\lion.shp'
GDB = r'\\dot55fp05\botplan\RIS\Data\Streets\LION\LION_Wild\17D\lion.gdb'


def guess_field_types(headers, data):
    fields = []
    geo_fields = set(['X', 'Y', 'LONGITUDE', 'LATITUDE', 'XF', 'YF', 'XT', 'YT'])
    for fn in headers:
        if fn in geo_fields:
            fields.append([fn, 'DOUBLE'])
        elif only_numbers(data, fn):
            fields.append([fn, 'LONG'])
        elif only_dates(data, fn):
            fields.append([fn, 'DATE'])
        else:
            fields.append([fn, 'TEXT'])
    return fields


def only_numbers(data, field):
    """
    assumes that the data is a list of dict objects and
    will test each value in data for given field
    :param data:
    :param field:
    :return:
    """
    for row in data:
        try:
            int(row[field])
        except:
            return False
    if field in ('SEGMENTID', 'NODEID'):
        return False
    return True


def only_dates(data, field):
    dates = False
    for row in data:
        if row[field]:
            if not type(row[field]) == datetime.datetime:
                return False
            else:
                dates = True
    return dates


def delete_shp(shp):
    if arcpy.Exists(shp):
        print 'Shapefile exists.\nDeleting %s...' % os.path.basename(shp)
        arcpy.Delete_management(shp)


def build_shp_schema(headers, data, full_path):
    # build shp schema
    fields = guess_field_types(headers, data)
    clean_fields = list()
    for f in fields:
        f_name, f_type = f
        if f_name == 'ID':
            f_name = 'ID_'
        if f_name == 'FID':
            f_name = 'ID__'
        if f_name == 'ON':
            f_name = 'ON_ST'
        if f_name == 'FROM':
            f_name = 'FROM_ST'
        if f_name == 'TO':
            f_name = 'TO_ST'
        # TODO: add fucntion to check if name exists and add int at end (too_long_1, too_long_2, etc)
        if len(f_name) > 9:  # shapefiles limit names, this truncates long names
            f_name = f[0][:9]
        f_name = f_name.replace(' ', '_')  # illegal characters
        f_name = f_name.replace('.', '_')
        clean_fields.append([f_name, f_type, f[0]])  # needed for dict of data
        arcpy.AddField_management(full_path, f_name, f_type)
    # add date and author
    arcpy.AddField_management(full_path, "AUTHOR", "TEXT")
    arcpy.AddField_management(full_path, "CREATED", "DATE")
    return clean_fields


def points(data, headers, output_name, output_loc=os.getcwd(), sref=SREFERENCE):
    # TODO: redefine spatial referance for upgraded arcpy so i can just pas srid
    # arcpy.SpatialReference(2263)
    user = getpass.getuser()
    total_lines = 0
    if '.shp' not in output_name:
        output_name += '.shp'
    output_name = output_name.replace('-', '_')
    full_path = os.path.join(output_loc, output_name)

    # delete previous version if exists
    delete_shp(full_path)

    print 'Creating Shapefile: %s in %s' % (output_name, output_loc)
    s_reference = arcpy.Describe(sref).spatialReference
    arcpy.CreateFeatureclass_management(output_loc, output_name, "POINT", "", "DISABLED", "DISABLED", s_reference)

    # build shp schema
    clean_fields = build_shp_schema(headers, data, full_path)

    rows = arcpy.InsertCursor(full_path)
    # populate data
    print 'Adding %i records...\n' % len(data)
    for line in data:
        if line:
            #print line
            row = rows.newRow()
            if not line['X']:
                line['X'] = 0
            if not line['Y']:
                line['Y'] = 0
            row.shape = arcpy.Point(line['X'], line['Y'])
            for field in clean_fields:
                # print col, fields[col][0], line[col]
                if field[1] == 'TEXT':
                    print field[0], str(line[field[2]])
                    line[field[0]] = str(line[field[2]])
                row.setValue(field[0], line[field[2]])
            row.setValue("AUTHOR", user)
            row.setValue("CREATED", datetime.datetime.now().strftime("%c"))
            rows.insertRow(row)
            total_lines += 1
    del rows
    print('\nDONE: Added %i rows of data to %s in folder %s\n' % (total_lines, output_name, output_loc))


def get_segment_geom(segment_list, lion='lion', gdb=GDB):
    seg_data = dict()
    arcpy.env.workspace = gdb
    segment_list = [i for i in segment_list if segment_validity([i])]
    segs = str(segment_list)[1:-1]
    arcpy.MakeFeatureLayer_management(lion, 'lion_working')
    arcpy.SelectLayerByAttribute_management("lion_working", "NEW_SELECTION", "SegmentID in (%s)" % segs)
    cur = arcpy.SearchCursor("lion_working", ["SegmentID", "XFrom", "YFrom", "XTo", "YTo"])
    for row in cur:
        seg, xf, yf = row.getValue("SegmentID"), row.getValue("XFrom"), row.getValue("YFrom")
        xt, yt = row.getValue("XTo"), row.getValue("YTo")
        seg_data[seg] = [xf, yf, xt, yt]
        print 'Getting geom for seg (%s) %s' % (seg, str(seg_data[seg]))
    arcpy.Delete_management('lion_working')
    return seg_data


def lines(data, headers, output_name, output_loc=os.getcwd(), geo_ref=SREFERENCE, strict=False):
    '''

    :param data: data list of dictionaries where keys match the headers
    :param headers: field names
    :param output_name: destination shp name
    :param geo_ref: lion file to get geometry from
    :param output_loc: destination folder
    :param strict: if True will only map stretches where whole stretch is valid
    :return:
    '''
# *****************************************************************************************************************
#     option 1:
#         pull nodes from json of block stretch and hit api again to get their coordinates to add to array
#             --- Doesn't seem possible, can get nodes of primary segment
#             --- (which seems to be garbage; see 79 st 34-35 aves) but not auxiliary segments
#     option 2:
#         select segments from shp and dissect their geometries - probably more accurate, but slow!
# *****************************************************************************************************************
#     TODO: add strict, make sure all segments are mapped or full record will not be mapped (avoids false positives)
    # get spatial referance from lion base file / geo referance
    s_reference = arcpy.Describe(geo_ref).spatialReference
    user = getpass.getuser()
    total_lines = 0
    if '.shp' not in output_name:
        output_name += '.shp'
    output_name = output_name.replace('-', '_')
    full_path = os.path.join(output_loc, output_name)

    # delete previous version if exists
    delete_shp(full_path)

    print 'Creating Shapefile: %s in %s' % (output_name, output_loc)
    arcpy.CreateFeatureclass_management(output_loc, output_name, "POLYLINE", "", "DISABLED", "DISABLED", s_reference)

    # build shp schema
    clean_fields = build_shp_schema(headers, data, full_path)
    rows = arcpy.InsertCursor(full_path)

    # populate data
    print 'Adding %i records...\n' % len(data)
    for line in data:
        if line:
            # print line
            row = rows.newRow()
            for geo_column in ('XF', 'YF', 'XT', 'YT'):
                if not line[geo_column]:
                    line[geo_column] = 0
            array = arcpy.Array()
            from_point = arcpy.Point(line['XF'], line['YF'])
            to_point = arcpy.Point(line['XT'], line['YT'])
            array.add(from_point)
            array.add(to_point)
            row.shape = arcpy.Polyline(array, s_reference)
            for field in clean_fields:
                if field[1] == 'TEXT':
                    if not line[field[2]]:
                        line[field[2]] = ''
                    line[field[0]] = str(line[field[2]])
                row.setValue(field[0], line[field[2]])
                row.setValue("AUTHOR", user)
                row.setValue("CREATED", datetime.datetime.now().strftime("%c"))
            rows.insertRow(row)
            # print 'inserted %s' % str(row)
            total_lines += 1
    del rows


def segment_validity(seg_list):
    """
    requires all segments to be valid
    """
    valid = True
    if not seg_list:
        return False
    for seg in seg_list:
        for char in seg:
            if ord(char) not in [ord(str(i)) for i in range(10)]:
                valid = False
    return valid
