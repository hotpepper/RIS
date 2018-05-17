__author__ = 'shostetter'
import requests
import re


PATH = 'http://dotvlvweb/LocationServiceAPI/api'  
#VERSION = '16D'


class BlockStretch:
    def __init__(self, on_street, cross_street_one, cross_street_two, borough, block_type='extendedstretch',
                 compass_direction_one='N', compass_direction_two='N'):
        self.OnStreet = on_street
        self.Borough = borough
        self.CrossStreetOne = str(cross_street_one)
        self.CrossStreetTwo = str(cross_street_two)
        self.CompassDirectionOne = compass_direction_one
        self.CompassDirectionTwo = compass_direction_two
        self.BlockType = block_type
        self.dir = 'N'
        self.segments = None
        self.node_list = list()
        self.json = self.get_segmentids()
        self.notes = None
        self.version = ''

    def block_stretch_request(self, direct=False):
        api_path = PATH+'/Block'
        print 'Geocoding %s (%s - %s)' % (self.OnStreet,  self.CrossStreetOne, self.CrossStreetTwo)
        self.boro_format()  # get formatted borough
        qry = {'OnStreet': self.OnStreet,
               'Borough': self.Borough,
               'CrossStreetOne': self.CrossStreetOne,
               'BoroughCrossStreetOne': self.Borough,
               'CrossStreetTwo': self.CrossStreetTwo,
               'BoroughCrossStreetTwo': self.Borough,
               'CompassDirectionOne': '',
               'CompassDirectionTwo': '',
               'BlockType': self.BlockType
               }
        if direct:
            qry['CompassDirectionOne'] = self.CompassDirectionOne
            qry['CompassDirectionTwo'] = self.CompassDirectionTwo
        # clean up formatting
        self.clean_up(qry)
        # get the results and try again if direction error
        output = requests.get(api_path, params=qry)
        return output.json()

    def clean_up(self, qry):
        if self.OnStreet:
            qry['OnStreet'] = self.OnStreet.replace(' ', '+')
        if self.CrossStreetOne:
            qry['CrossStreetOne'] = self.CrossStreetOne.replace(' ', '+')
        if self.CrossStreetTwo:
            qry['CrossStreetTwo'] = self.CrossStreetTwo.replace(' ', '+')

    def boro_format(self):
        dictionary = {'K': 'BROOKLYN', 'Q': 'QUEENS', 'M': 'MANHATTAN', 'X': 'BRONX', 'S': 'STATEN ISLAND',
                      '3': 'BROOKLYN', '4': 'QUEENS', '1': 'MANHATTAN', '2': 'BRONX', '5': 'STATEN ISLAND',
                      'BK': 'BROOKLYN', 'QN': 'QUEENS', 'MN': 'MANHATTAN', 'BX': 'BRONX', 'SI': 'STATEN ISLAND'
                      }
        self.Borough = str(self.Borough).upper()
        try:
            self.Borough = str(int(self.Borough))
        except:
            pass
        if self.Borough in dictionary.keys():
            self.Borough = dictionary[self.Borough]

    def direction_binary(self, direction):
        # TODO: add a note to records where direction was guessed!
        print 'Direction Binary Triggered...'
        if direction == 'N':
           direction = 'E'
        else:
            direction = 'N'
        self.notes = 'Guessed Direction (%s)' % self.dir
        return direction

    def first_error(self, json_data):
        if 'BlockFaceList' not in json_data.keys():
            self.CompassDirectionOne = self.direction_binary(self.CompassDirectionOne)
            json_data = self.block_stretch_request(True)
        if 'BlockFaceList' not in json_data.keys():
            self.CompassDirectionOne = self.direction_binary(self.CompassDirectionOne)
            json_data = self.block_stretch_request(True)
        if 'BlockFaceList' not in json_data.keys():
            self.CompassDirectionTwo = self.direction_binary(self.CompassDirectionTwo)
            json_data = self.block_stretch_request(True)
        if 'BlockFaceList' not in json_data.keys():
            self.CompassDirectionTwo = self.direction_binary(self.CompassDirectionTwo)
            json_data = self.block_stretch_request(True)
        return json_data

    def get_segmentids(self):
        json_data = self.block_stretch_request()
        segs = []
        json_data = self.first_error(json_data)
        if 'BlockFaceList' not in json_data.keys():
            # print json_data['ErrorDetails']
            if 'GeoSupportError' in json_data:
                segs.append(json_data['GeoSupportError'])
        else:
            for block in json_data['BlockFaceList']:
                # print block
                # if 'SegmentID' in block.keys():
                #     segs.append(block['SegmentID'])
                if 'FromNode' in block.keys():
                    self.node_list.append(block['FromNode'])
                    self.node_list.append(block['ToNode'])
                if 'AuxiliarySegmentIds' in block.keys():
                    for s in block['AuxiliarySegmentIds']:
                        segs.append(s)
                else:
                    segs.append(block['GeoSupportError'])
        self.segments = [str(seg) for seg in segs]
        if 'Version' in json_data.keys():
            self.version = json_data['Version']  # bug fix for missing version on bad borough API requests
        else:
            self.version = ''
        return json_data


class Intersection(object):
    def __init__(self, street1, street2, boro, direction=''):
        self.dir = direction
        self.street1 = street1
        self.street2 = street2
        self.Borough = boro
        self.json = None
        self.notes = None
        self.storage = {'street1': None,
                        'street2': None,
                        'boro': None,
                        'x': None,
                        'y': None,
                        'lion node': None,
                        'error': None,
                        'zip code': None,
                        'community district': None,}
        self.get_nodes()
        if self.json:
            if 'Version' in self.json.keys():
                self.version = self.json['Version']  # bug fix for missing version on bad borough API requests
            else:
                self.version = ''
        else:
            self.version = ''

    def direction_binary(self):
        # TODO: add a note to records where direction was guessed!
        print 'Direction Binary Triggered...'

        if self.dir == 'N':
            self.dir = 'E'
        else:
            self.dir = 'N'
        self.notes = 'Guessed Direction (%s)' % self.dir

    def boro_format(self):
        dictionary = {'K': 'BROOKLYN', 'Q': 'QUEENS', 'M': 'MANHATTAN', 'X': 'BRONX', 'S': 'STATEN ISLAND',
                      '3': 'BROOKLYN', '4': 'QUEENS', '1': 'MANHATTAN', '2': 'BRONX', '5': 'STATEN ISLAND',
                      'BK': 'BROOKLYN', 'QN': 'QUEENS', 'MN': 'MANHATTAN', 'BX': 'BRONX', 'SI': 'STATEN ISLAND'
                      }
        self.Borough = str(self.Borough).upper()
        if self.Borough in dictionary.keys():
            self.Borough = dictionary[self.Borough]

    def intersection_request(self):
        print 'Mapping %s & %s' % (self.street1, self.street2)
        api_path = PATH+'/Intersection'
        self.boro_format()
        qry = {'CrossStreetOne': self.street1.replace(' ', '+'),
               'CrossStreetTwo': self.street2.replace(' ', '+'),
               'Borough': self.Borough,
               'BoroughCrossStreetOne': self.Borough,
               'BoroughCrossStreetTwo': self.Borough}  # ,'CompassDirection': self.dir

        # get the results and try again if direction error
        output = requests.get(api_path, params=qry)
        attempts = 0
        while attempts < 3 and 'LionNodeNumber' not in output.json().keys():
            if 'GeoSupportError' in output.json().keys():
                # assumes more than 1 intersection, if they are close then apply random dir
                if error_find_dist(output.json()['GeoSupportError']):
                    self.direction_binary()
                    qry['CompassDirection'] = self.dir
                    output = requests.get(api_path, params=qry)
                # 1st direction guess was wrong, try other
                elif output.json()['GeoSupportError'] == u'COMPASS DIRECTION VALUE IS INVALID FOR THIS INPUT LOCATION':
                    self.direction_binary()
                    qry['CompassDirection'] = self.dir
                    output = requests.get(api_path, params=qry)
                    attempts += 1
                else:
                    # too far to guess at direction
                    # check if direction supplied
                    if self.dir:
                        print 'attempts %i' % attempts
                        qry['CompassDirection'] = self.dir
                        output = requests.get(api_path, params=qry)
                        if 'GeoSupportError' not in output.json().keys():
                            print 'Using supplied direction'
                    attempts += 2
            attempts += 1
        if 'GeoSupportError' in output.json().keys() and attempts > 0:
            print output.json()['GeoSupportError']
            self.storage['error'] = output.json()['GeoSupportError']
        return output.json()

    def get_nodes(self):
        if self.street1 and self.street2:
            self.json = self.intersection_request()
            if 'XCoordinate' in self.json.keys():  # indicates the request was successful
                self.storage['street1'] = self.json['CrossStreetOne'].keys()[0]
                self.storage['street2'] = self.json['CrossStreetTwo'].keys()[0]
                self.storage['boro'] = self.json['CrossStreetOne'][self.storage['street1']]['BoroughName']
                self.storage['x'] = int(self.json['XCoordinate'])
                self.storage['y'] = int(self.json['YCoordinate'])
                self.storage['lion node'] = self.json['LionNodeNumber']
                self.storage['zip code'] = self.json['ZipCode']
                self.storage['community district'] = self.json[u'CommunityDistrict'][u'BoroughCode'] + \
                                                     self.json[u'CommunityDistrict'][u'DistrictNumber']

            elif 'ErrorDetails'in self.json.keys():
                self.storage['street1'] = self.street1
                self.storage['street2'] = self.street2
                self.storage['boro'] = self.Borough
                self.storage['error'] = self.intersection_request()['ErrorDetails']
            else:
                self.storage['street1'] = self.street1
                self.storage['street2'] = self.street2
                self.storage['boro'] = self.Borough


class Addrresses(object):
    def __init__(self, house_number, street, boro):
        self.dir = 'N'
        self.HouseNumber = str(house_number).replace('-', '')
        self.HouseNumber = str(int(float(self.HouseNumber))).replace('.', '')
        self.Street = street
        self.Borough = boro
        self.json = None
        self.notes = None
        self.storage = {'HouseNumber': self.HouseNumber,
                        'Street': None,
                        'SegmentId': None,
                        'boro': None,
                        'LowCrossStreets': None,
                        'HighCrossStreets': None,
                        'x': None,
                        'y': None,
                        'error': None,
                        'PolicePrecinct': None}
        self.get_data()
        if 'Version' in self.json.keys():
            self.version = self.json['Version']  # bug fix for missing version on bad borough API requests
        else:
            self.version = ''

    def boro_format(self):
        dictionary = {'K': 'BROOKLYN', 'Q': 'QUEENS', 'M': 'MANHATTAN', 'X': 'BRONX', 'S': 'STATEN ISLAND',
                      '3': 'BROOKLYN', '4': 'QUEENS', '1': 'MANHATTAN', '2': 'BRONX', '5': 'STATEN ISLAND',
                      'BK': 'BROOKLYN', 'QN': 'QUEENS', 'MN': 'MANHATTAN', 'BX': 'BRONX', 'SI': 'STATEN ISLAND'
                      }
        self.Borough = str(self.Borough).upper()
        if self.Borough in dictionary.keys():
            self.Borough = dictionary[self.Borough]

    def address_request(self):

        print 'Mapping %s %s' % (self.HouseNumber, self.Street)
        api_path = PATH+'/ExactAddress'
        # http://dotvlvweb/LocationServiceAPI/api/ExactAddress?HouseNumber=3440+&Street=79+st&Borough=Queens&ZipCode=
        self.boro_format()
        qry = {'HouseNumber': str(self.HouseNumber).replace(' ', '+'),
               'Street': self.Street.replace(' ', '+'),
               'Borough': self.Borough}
        output = requests.get(api_path, params=qry)
        return output.json()

    def get_data(self):
        self.json = self.address_request()
        if 'XCoordinate' in self.json.keys():  # indicates the request was successful
            self.storage['Street'] = self.json['Street'].keys()[0]
            self.storage['SegmentId'] = self.json['SegmentId']
            self.storage['boro'] = self.json['CommunityDistrict']['BoroughName']
            self.storage['x'] = int(self.json['XCoordinate'])
            self.storage['y'] = int(self.json['YCoordinate'])
            if 'LowCrossStreets' in self.json.keys():
                self.storage['LowCrossStreets'] = self.json['LowCrossStreets'][0].keys()[0]
            if 'HighCrossStreets' in self.json.keys():
                self.storage['HighCrossStreets'] = self.json['HighCrossStreets'][0].keys()[0]
            self.storage['PolicePrecinct'] = self.json['PolicePrecinct']

        elif 'ErrorDetails'in self.json.keys():
            self.storage['Street'] = self.Street
            self.storage['HouseNumber'] = self.HouseNumber
            self.storage['boro'] = self.Borough
            self.storage['error'] = self.address_request()['ErrorDetails']
        else:
            self.storage['Street'] = self.Street
            self.storage['HouseNumber'] = self.HouseNumber
            self.storage['boro'] = self.Borough
            self.storage['error'] = self.address_request()['GeoSupportError']


class Node(object):
    def __init__(self, nodeid):
        self.nodeid = nodeid
        self.json = None
        self.notes = None
        self.storage = {'street1': None,
                        'street2': None,
                        'boro': None,
                        'x': None,
                        'y': None,
                        'lion node': None,
                        'error': None,
                        'zip code': None,
                        'community district': None}
        self.get_coords()
        if 'Version' in self.json.keys():
            self.version = self.json['Version']  # bug fix for missing version on bad borough API requests
        else:
            self.version = ''

    def node_request(self):
        api_path = PATH+'/Intersection'
        qry = {'NodeId': self.nodeid}
        # get the results and try again if direction error
        output = requests.get(api_path, params=qry)
        if 'GeoSupportError' in output.json().keys():
            print output.json()['GeoSupportError']
            self.storage['error'] = output.json()['GeoSupportError']
        return output.json()

    def get_coords(self):
        self.json = self.node_request()
        if 'XCoordinate' in self.json.keys():  # indicates the request was successful
            self.storage['street1'] = self.json['IntersectingStreets'].keys()[0]
            if len(self.json['IntersectingStreets'].keys()) > 1:
                self.storage['street2'] = self.json['IntersectingStreets'].keys()[1]
            else:
                self.storage['street2'] = ''
            self.storage['boro'] = self.json['IntersectingStreets'][self.storage['street1']]['BoroughName']
            self.storage['x'] = int(self.json['XCoordinate'])
            self.storage['y'] = int(self.json['YCoordinate'])
            self.storage['lion node'] = self.json['LionNodeNumber']
            self.storage['zip code'] = self.json['ZipCode']
            self.storage['community district'] = self.json[u'CommunityDistrict'][u'BoroughCode'] + \
                                                 self.json[u'CommunityDistrict'][u'DistrictNumber']


def error_find_dist(string, dist_tollerance=500):
    dist_s = re.findall(r'[0-9]* FT', string)
    if dist_s:
        dist_n = [int(s) for s in dist_s[0].split() if s.isdigit()]
        if dist_n:
            if int(dist_n[0]) < dist_tollerance:
                return True
            else:
                return False
        else:
            return False
    else:
        return False


def test_cases():
    print '_'*30
    print 'Testing Corridors'
    print '-'*30
    bs = BlockStretch('Roosevelt Ave', '74 St', 'Junction Blvd', 4)
    assert bs.json.keys() == [u'Version', u'Grc', u'NumberOfIntersections', u'CrossStreetOne',
                              u'CrossStreetTwo', u'BlockFaceList', u'OnStreet']
    bs = BlockStretch('W 110 St', 'Broadway', 'Lenox Ave', 'M')
    assert bs.json.keys() == [u'Version', u'Grc', u'NumberOfIntersections', u'CrossStreetOne',
                              u'CrossStreetTwo', u'BlockFaceList', u'OnStreet']
    bs = BlockStretch('172 st', 'hillside Ave', 'Jamaica Av', 'Q')
    assert bs.json.keys() == [u'Version', u'Grc', u'NumberOfIntersections', u'CrossStreetOne',
                              u'CrossStreetTwo', u'BlockFaceList', u'OnStreet']
    print 'Corridors Test Successful'
    print '_'*30
    print 'Testing Intersections'
    print '-'*30
    i = Intersection('Junction Blvd', 'roosevelt ave', 'Q')
    assert i.json.keys() == [u'CommunityDistrict', u'XCoordinate', u'PolicePrecinct',
                             u'CityCouncilDistrict', u'IntersectingStreets', u'LionNodeNumber',
                             u'ZipCode', u'Longitude', u'YCoordinate', u'SchoolDistrict', u'Grc',
                             u'ReasonCode', u'Latitude', u'CrossStreetOne', u'CrossStreetTwo',
                             u'AssemblyDistrict', u'GeoSupportWarning']
    i = Intersection('W 110 St', 'Broadway', 'MN')
    assert i.json.keys() == [u'CommunityDistrict', u'XCoordinate', u'PolicePrecinct',
                             u'CityCouncilDistrict', u'IntersectingStreets', u'LionNodeNumber',
                             u'ZipCode', u'Longitude', u'YCoordinate', u'SchoolDistrict', u'Grc',
                             u'ReasonCode', u'Latitude', u'CrossStreetOne', u'CrossStreetTwo',
                             u'AssemblyDistrict', u'GeoSupportWarning']
    print i.storage['lion node'], i.storage['x'], i.storage['y']
    i = Intersection('Alderton St', 'Ellwell Crescent', 'Q')
    assert i.json.keys() == [u'CrossStreetOne', u'CrossStreetTwo', u'Grc', u'GeoSupportError']
    i = Intersection('Alderton St', 'Ellwell Crescent', 'Q', 'N')
    assert i.json.keys() == [u'CommunityDistrict', u'XCoordinate', u'PolicePrecinct',
                             u'CityCouncilDistrict', u'IntersectingStreets', u'LionNodeNumber',
                             u'ZipCode', u'Longitude', u'YCoordinate', u'SchoolDistrict', u'Grc',
                             u'ReasonCode', u'Latitude', u'CrossStreetOne', u'CrossStreetTwo',
                             u'AssemblyDistrict', u'GeoSupportWarning']
    i = Intersection('broadway', 'justice av', 'Q')
    assert i.json.keys() == [u'CommunityDistrict', u'XCoordinate', u'PolicePrecinct',
                             u'CityCouncilDistrict', u'IntersectingStreets', u'LionNodeNumber',
                             u'ZipCode', u'Longitude', u'YCoordinate', u'SchoolDistrict', u'Grc',
                             u'ReasonCode', u'Latitude', u'CrossStreetOne', u'CrossStreetTwo',
                             u'AssemblyDistrict', u'GeoSupportWarning']
    print i.storage['lion node'], i.storage['x'], i.storage['y']
    i = Intersection('Myrtle Ave', '66th Pl', 'QN')
    assert i.json.keys() == [u'CommunityDistrict', u'XCoordinate', u'PolicePrecinct',
                             u'CityCouncilDistrict', u'IntersectingStreets', u'LionNodeNumber',
                             u'ZipCode', u'Longitude', u'YCoordinate', u'SchoolDistrict', u'Grc',
                             u'ReasonCode', u'Latitude', u'CrossStreetOne', u'CrossStreetTwo',
                             u'AssemblyDistrict', u'GeoSupportWarning']
    print 'Intersections Test Successful'
    print '_'*30
    print 'Testing Addresses'
    print '-'*30
    a = Addrresses('3440', '79th st', 'Q')
    assert a.storage == {'boro': u'QUEENS',
                         'HouseNumber': '3440',
                         'Street': u'79 STREET',
                         'SegmentId': u'0175322',
                         'y': 213478,
                         'x': 1015370,
                         'PolicePrecinct': u'115',
                         'HighCrossStreets': u'35 AVENUE',
                         'LowCrossStreets': u'34 AVENUE',
                         'error': None}
    a = Addrresses('55', 'water', 1)
    assert a.storage == {'boro': 'MANHATTAN',
                         'HouseNumber': '55',
                         'Street': 'WATER STREET',
                         'SegmentId': '0023137',
                         'x': 981538,
                         'y': 195616,
                         'PolicePrecinct': '001',
                         'HighCrossStreets': 'HANOVER SQUARE',
                         'LowCrossStreets': 'COENTIES SLIP',
                         'error': None}
    print 'Address Test Successful'
    print '_'*30
    print '*'*50
    print '%sTESTING COMPLETE' % (' '*((50 - len('TESTING COMPLETE'))/2))
    print '*'*50

if __name__ == '__main__':
    test_cases()
    # bs = BlockStretch('justice ave', 'broadway', '55 ave', 4)
    # a = Addrresses('1', 'pennyfield av', 'x')

