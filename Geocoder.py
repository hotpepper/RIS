
from ReadInput import DataFile as Df
from GeoSupportAPI import *
from shapify import *
from Tkinter import Tk
import tkMessageBox


def run(file_path=None):
    # get file (excle (old/new) or csv)
    if file_path:
        data_file = Df(file_path)
    else:
        data_file = Df()

    mapping_type = raw_input("""\nWhat type of geocoding is needed?\n\n%s\n\t1: Intersection('STREET 1', 'STREET 2', 'BOROUGH)\n\t2: Address ('NUMBER', 'STREET', 'BOROUGH' OR 'ADDRESS', 'BOROUGH')
    \t3: On-From-To ('STREET 1', 'STREET 2', 'STREET 3', 'BOROUGH')\n\t4: Coordinates from Nodes \n%s\nEnter Selection Number: """ % ('*'*50, '*'*50))
    if mapping_type == '1':
        print "Required field names: 'STREET 1', 'STREET 2', 'BOROUGH'\n"
        intersection(data_file)
    elif mapping_type == '2':
        print "Required field names: 'NUMBER', 'STREET', 'BOROUGH' \nOR 'ADDRESS', 'BOROUGH'\n"
        address(data_file)
    elif mapping_type == '3':
        print "Required field names: 'STREET 1', 'STREET 2', 'STREET 3', 'BOROUGH'\n"
        block(data_file)
    elif mapping_type == '4':
        nodes(data_file)
    else:
        print '\n\tNO VALID SELECTION MADE...\n'
    print "~"*75
    print '\nDONE\n'
    print "~"*75


def intersection(data_file):
    print '%i worksheets with intersection data found' % len(data_file.tabs_with_intersection_min())
    for tab in data_file.tabs_with_intersection_min():
        # add fields to headers
        data_file.data[tab].headers += ['NODE', 'X', 'Y', 'ERROR']
        for row in data_file.data[tab].data:
            i = Intersection(row['STREET 1'], row['STREET 2'], row['BOROUGH'])
            node, x, y, error = i.storage['lion node'], i.storage['x'], i.storage['y'], i.storage['error']
            # add geo to data
            row['NODE'] = node
            row['X'] = x
            row['Y'] = y
            row['ERROR'] = error
            row['NOTES'] = i.notes
            row['VERSION'] = i.version
        headers = data_file.data[tab].headers
        headers += ['NOTES', 'VERSION']
        data = data_file.data[tab].data
        points(data, headers, data_file.data[tab].sheet_name, data_file.data[tab].file_path)


def address(data_file):
    print '%i worksheets with address data found' % len(data_file.tabs_with_addresses_min())
    for tab in data_file.tabs_with_addresses_min():
        data_file.data[tab].headers += ['SEGMENTID', 'X', 'Y', 'ERROR']
        for row in data_file.data[tab].data:
            a = Addrresses(row['NUMBER'], row['STREET'], row['BOROUGH'])
            seg, x, y, error = a.storage['SegmentId'], a.storage['x'], a.storage['y'], a.storage['error']
            # add fields to headers
            # add geo to data
            row['SEGMENTID'] = seg
            row['X'] = x
            row['Y'] = y
            row['ERROR'] = error
            row['NOTES'] = a.notes
            row['VERSION'] = a.version
        headers = data_file.data[tab].headers
        headers += ['NOTES']
        headers += ['NOTES', 'VERSION']
        data = data_file.data[tab].data
        points(data, headers, data_file.data[tab].sheet_name, data_file.data[tab].file_path)


def block(data_file):
    print '%i worksheets with block data found' % len(data_file.tabs_with_stretch_min())
    for tab in data_file.tabs_with_stretch_min():
        new_data = list()
        data_file.data[tab].headers += ['SEGMENTID', 'XF', 'YF', 'XT', 'YT', 'ERROR']
        for row in data_file.data[tab].data:
            if type(row['BOROUGH']) == float:
                row['BOROUGH'] = str(int(row['BOROUGH']))
            if set(['ON', 'FROM', 'TO']).issubset(set(data_file.data[tab].headers)):
                c = BlockStretch(row['ON'], row['FROM'], row['TO'], row['BOROUGH'])
            elif set(['ON STREET', 'FROM STREET', 'TO STREET']).issubset(set(data_file.data[tab].headers)):
                c = BlockStretch(row['ON STREET'], row['FROM STREET'], row['TO STREET'], row['BOROUGH'])
            elif set(['STREET 1', 'STREET 2', 'STREET 3']).issubset(set(data_file.data[tab].headers)):
                c = BlockStretch(row['STREET 1'], row['STREET 2'], row['STREET 3'], row['BOROUGH'])
            segmentids = c.segments
            # check fo valid segs
            segmentids = [i for i in segmentids if segment_validity([i])]
            # get xy from and to from lion via shapify
            if segmentids:
                geo = get_segment_geom(segmentids)
                # print row['STREET 1']
                for seg in geo.keys():
                    if segment_validity([seg]):
                        row['SEGMENTID'] = seg
                        row['XF'], row['YF'], row['XT'], row['YT'] = geo[seg]
                        row['ERROR'] = None
                    else:
                        row['SEGMENTID'] = seg
                        row['XF'], row['YF'], row['XT'], row['YT'] = 0, 0, 0, 0
                        row['ERROR'] = seg
                    row['NOTES'] = c.notes
                    row['VERSION'] = c.version
                    new_data.append(dict(row))
            else:
                row['SEGMENTID'] = None
                row['XF'], row['YF'], row['XT'], row['YT'] = None, None, None, None
                # print c.segments
                if c.segments:
                    row['ERROR'] = c.segments[0]
                else:
                    row['ERROR'] = None
                row['NOTES'] = c.notes
                row['VERSION'] = c.version
                new_data.append(dict(row))
        headers = data_file.data[tab].headers
        headers += ['NOTES', 'VERSION']
        data = new_data
        lines(data, headers, data_file.data[tab].sheet_name, data_file.data[tab].file_path)


def nodes(data_file):
    print '%i worksheets with node data found' % len(data_file.tabs_with_nodes_min())
    for tab in data_file.tabs_with_nodes_min():
        for row in data_file.data[tab].data:
            if type(row['NODEID']) == float:
                row['NODEID'] = int(row['NODEID'])
                print row['NODEID']
            n = Node(row['NODEID'])
            street1 = n.storage['street1']
            street2 = n.storage['street2']
            boro = n.storage['boro']
            x = n.storage['x']
            y = n.storage['y']
            error = n.storage['error']
            zc = n.storage['zip code']
            cd = n.storage['community district']
            # add fields to headers
            data_file.data[tab].headers += ['X', 'Y', 'ERROR', 'STREET1', 'STREET2', 'BOROUGH', 'ZIP', 'COM_DIST']
            # add geo to data
            row['X'] = x
            row['Y'] = y
            row['ERROR'] = error
            row['STREET1'] = street1
            row['STREET2'] = street2
            row['BOROUGH'] = boro
            row['ZIP'] = zc
            row['COM_DIST'] = cd
            row['NOTES'] = n.notes
            row['VERSION'] = n.version
        headers = data_file.data[tab].headers
        headers += ['NOTES', 'VERSION']
        data = data_file.data[tab].data
        points(data, headers, data_file.data[tab].sheet_name, data_file.data[tab].file_path)


if __name__ == '__main__':
    try:
        print '\nStarting up...\n'
        run()
        Tk().withdraw()
        tkMessageBox.showinfo("Finished", "Finished Geocoding Data")
    except (RuntimeError, TypeError, NameError, IOError, ValueError, KeyError) as e:
        print '\nERROR\n'
        err = raw_input(e)
