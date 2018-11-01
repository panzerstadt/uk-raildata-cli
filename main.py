import pandas as pd
import json

# main ref: http://www.railwaycodes.org.uk/index.shtml
# data source: http://data.atoc.org/data-download

"""
Master Stations Names File
This contains details of all public stations, ferry terminals and bus stops for services from ITPS and the manual trains file.
The file consists of various record types in the following order:
Header
For Each Station
    For Each TIPLOC for station 1 Station Detail record
        0, 1, 2, 3 or 4 Table number records
        0 or 1 Comment Record (only written for first TIPLOC for a station)
    End For
End For
All Alias records
All Group records
All Connection records
All Routeing Group records Trailer 1
Trailer 2
Trailer 3
Trailer 4
440 3-Alpha usage records Trailer 5
"""

"""
Name 	               Length 	Description
----                   ------   -----------
Record Type 	            1	“A”
Spaces 	                    4	Spaces
Station Name                30	Station Name
CATE Type 	                1	Interchange Status. Values:
                                0 Not an interchange Point
                                1 Small Interchange Point
                                2 Medium Interchange Point
                                3 Large Interchange Point
                                9 This is a subsidiary TIPLOC at a station which has more than one TIPLOC. Stations which have more than one TIPLOC always have the same principal 3- Alpha Code.
                                This field enables a Timetables enquiry system to give some precedence for changing at large interchange points ahead of medium interchange points ahead of small interchange points.
TIPLOC code 	            7	Location code as held in the CIF data
Subsidiary 3- Alpha code 	3	Where a station has more than one TIPLOC e.g. Tamworth, this is set to the 3-Alpha Code that is not in the field below. Normally this is a repeat of the 3-Alpha Code
Spaces 	                    3	Spaces
3-Alpha Code 	            3	Principal 3-Alpha Code of Station. Part of location code for the manual trains CIF data
Easting 	                5	Easting in units of 100m. Stations too far south (Channel Islands) or too far north (Orkneys) or too far west (west of Carrick on Shannon) have both their Easting and Northing set to 00000. The most westerly station in range, Carrick on Shannon, has value 10000. The most easterly station, Amsterdam, has value 18690.
Estimated 	                1	“E” means estimated coordinates, space otherwise
Northing 	                5	Northing in units of 100m. Stations too far south (Channel Islands) or too far north (Orkneys) or too far west (west of Carrick on Shannon) have both their Easting and Northing set to 00000. The most southerly station in range, Lizard (Bus), has value 60126. The most northerly station in range, Scrabster, has value 69703.
Change Time 	            2	Change time in minutes
Footnote 	                2	CATE footnote. This data is historic, is not maintained and should be ignored.
Spaces 	                    11	Spaces
Region 	                    3	Sub-sector code. One of about 80 geographical region codes. This data is historic, is not maintained and should be ignored.
Space 	                    1	Space
"""


# train UIDs are used to identify trains on this API


def search_by_train(train_uid="W64533", date_str="2018-10-30", show_json=True):
    import requests
    import json

    url = "https://fcc.transportapi.com/v3/uk/train/service/train_uid:{}/{}/timetable.json?live=true".format(
        train_uid, date_str)

    print('searching train by GET: {}'.format(url))
    r = requests.get(url).json()
    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    return r


def search_by_station(station_CRS="ZFD", count=10, show_json=True):
    import requests
    import json

    url = "https://fcc.transportapi.com/v3/uk/train/station/{}/live.json?limit={}".format(
        station_CRS, count)

    print('searching station by GET: {}'.format(url))
    r = requests.get(url).json()
    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    return r


def parse_CRS(debug=False):
    # ref: http://data.atoc.org/sites/all/themes/atoc/files/rsps5041%20-%20Timetable%20Data.pdf
    filepath = "./data/ttis074/ttisf074.msn"
    # every row in the .msn file is 82 characters

    # json structure suggested
    output_json_structure = {
        "names": ["ABERDARE", "ABERDAR"],
        "interchange_status": 0,
        "TIPLOC": "ABDARE",
        "CRS": {
            "main": "ABA",
            "secondary": "ABA"
        },
        "coordinates": {
            "easting": 13004,
            "northing": 62027,
            "is_estimate": 0
        },
        "change_time": 3
    }

    interchange_status_structure = {
        0: "none",
        1: "small",
        2: "medium",
        3: "large",
        9: "This is a subsidiary TIPLOC at a station which has more than one TIPLOC. Stations which have more than one TIPLOC always have the same principal 3- Alpha Code."
    }

    with open(filepath) as f:
        dataset = f.readlines()
    header = dataset[0]

    content = dataset[1:]
    content = [c.strip('\n') for c in content]

    # we only want to get record type "A" and record type "L"
    # type A is the main train station reference data (station details)
    # type L is the alias data

    # the below are indices. to slice, the end_index = end_index + 1
    msn_record_pos = {
        "record_type": [0],
        "station_name": [5, 34],
        "interchange_size": [35],
        "TIPLOC": [36, 42],
        "CRS_secondary": [43, 45],
        "CRS_main": [49, 51],
        "easting": [52, 56],
        "is_estimate": [57],
        "northing": [58, 62],
        "change_time": [64]
    }

    def print_record(key, value):
        print("{:10}: {}".format(key, value))

    output = []
    for c in content:
        record_dict = {}
        # parse record type A
        record_type = msn_record_pos["record_type"][0]
        type_check = c[record_type]

        # based on type, parse content, c
        if type_check.lower() == "a":
            for k, v in msn_record_pos.items():
                if len(v) == 1:
                    if debug:
                        print_record(k, c[v[0]])
                    record_value = c[v[0]]
                    # format interchange_size
                    if k == "interchange_size":
                        try:
                            record_value = interchange_status_structure[int(
                                record_value)]
                        except:
                            raise SystemExit(
                                'interchange type unknown. interchange code:{}'.format(record_value))
                    # format is_estimate
                    elif k == "is_estimate":
                        if record_value.lower() == "e":
                            record_value = "1"
                        else:
                            record_value = "0"
                else:
                    if debug:
                        print_record(k, c[v[0]:v[-1]+1])
                    record_value = c[v[0]:v[-1] + 1]  # +1 because slice

                record_value = record_value.strip()
                record_dict[k] = record_value
            output.append(record_dict)

    # save type A record
    with open('temp.json', "w") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    # parse record type L


def station_from_CRS(dict_file="temp.json", crs="COV", show_json=True):
    output = []
    with open(dict_file) as f:
        station_names = json.load(f)

    for s in station_names:
        if s['CRS_main'] == crs.upper() or s['CRS_secondary'] == crs.upper():
            output.append(s)

    if show_json:
        print(json.dumps(output, indent=4, ensure_ascii=False))

    return output


def station_from_TIPLOC(dict_file="temp.json", tiploc="ABWD", show_json=True):
    output = []
    with open(dict_file) as f:
        station_names = json.load(f)

    for s in station_names:
        if s['TIPLOC'] == tiploc.upper():
            output.append(s)

    if show_json:
        print(json.dumps(output, indent=4, ensure_ascii=False))

    return output


def station_from_name(dict_file="temp.json", station_name="coventry", show_json=True):
    output = []
    with open(dict_file) as f:
        station_names = json.load(f)

    for s in station_names:
        if station_name.upper() in s["station_name"]:
            output.append(s)

    if show_json:
        print(json.dumps(output, indent=4, ensure_ascii=False))

    return output


def main():
    parse_CRS()


def describe():
    # ref: https://www.railforums.co.uk/threads/train-id-codes-but-not-headcodes.85651/
    main_description = """
    things to know
    data source
        - http://data.atoc.org/data-download
        - updated every week
    trains
        - train_uid -> W64717
        - train service code -> 22728000
    stations
        - CRS -> ZFD
        - TIPLOC -> STALBCY
    station search by geolocation
        - https://developer.transportapi.com/docs?raml=https://transportapi.com/v3/raml/transportapi.raml##uk_places_json
    updates fares data
        - http://data.atoc.org/fares-data
    """

    def describe_trains():
        # reader: http://smethur.st/posts/37194017

        train_search = "to search for trains, you can use either the [train's service code] or [train_uid code],\nboth of which can be found on live/timetabled service updates at the station."""

        json_example = """
        example from json:
        ----------------------
        "service": "22728000",
        "train_uid": "W64717",
        .
        .
        .
        ----------------------
        """

        train_uid = "[train_uid] train_uid is the unique identifier for passenger trains, used in reservation systems"
        train_uid_extra = "The GR4180 is a unique ID for the reservation system, AFAIK it only contains passenger services... The number is printed on Reservation slips and some trains display it on the external displays (22x & 390)"
        train_service_code = "[train service code] a 8 digit number denoting the current train service. it changes frequently based on dates"

        print()
        print('-'*100)
        print('TRAINS')
        print('-'*100)
        print(train_search)
        print(json_example)
        print(train_uid, "ref: '{}'".format(train_uid_extra))
        print()
        print(train_service_code)
        print()

    def describe_stations():
        # ref: https://wiki.openraildata.com/index.php/Identifying_Locations
        # ref: http://www.railwaycodes.org.uk/crs/CRS0.shtm
        CRS = """[CRS] CRS or NRS or 3Alpha codes are three character codes to describe stations.
        a station may have more than 1 CRS code."""
        TIPLOC = "[TIPLOC] code used by train planners to calculate train timing. max 7 characters."
        description = "There are two types of station codes of note: [CRS] and [TIPLOC]"

        print('-'*100)
        print('STATIONS')
        print('-'*100)
        print(description)
        print(CRS)
        print()
        print(TIPLOC)
        print()

    def describe_misc():
        # ref: http://www.railwaycodes.org.uk/crs/CRS0.shtm
        CRS_in = "ZFD"
        source_of_truth = "http://ojp.nationalrail.co.uk/service/ldbboard/dep/" + CRS_in

        description = "the ultimate source of truth for station data can be tracked to the website's live departure boards, e.g. {}".format(
            source_of_truth)

        print(description)

        full_station_list = "http://www.realtimetrains.co.uk/train/W64717/2018/06/04/advanced"

        description = "there are also full station lists (dunno where to find them yet). an example can be seen here: {}".format(
            full_station_list)

        print(description)

    print('\n\n\n')
    print('-'*100)
    print('UK railways API search summary')
    print('-'*100)
    describe_stations()
    describe_trains()
    describe_misc()

    print()
    print('-'*100)
    print('SUMMARY')
    print('-'*100)
    print(main_description)


def sample():
    from datetime import date

    today_str = str(date.today())
    station = "ZFD"

    print()
    print('-'*100)
    print('SAMPLE')
    print('-'*100)
    print('sample case')
    print('this searches for 10 trains for station: {} on date: {}'.format(
        station, today_str))
    search_by_station(show_json=True)


def CLI():
    print('search for station data by CRS or station name:')
    chk = input(
        '1. by CRS\n2. by station TIPLOC\n3. by station name\n9. help documentation for these weird acronyms\nchoice:_')

    station_data = None
    if int(chk) == 1:
        print('searching by CRS')
        param = input('please input CRS code:_')
        station_data = station_from_CRS(crs=param)
    elif int(chk) == 2:
        print('searching by TIPLOC')
        param = input('please input TIPLOC code:_')
        station_data = station_from_TIPLOC(tiploc=param)
    elif int(chk) == 3:
        print('searching by station name')
        param = input('please input station name:_')
        station_data = station_from_name(station_name=param)
    elif int(chk) == 9:
        describe()

    if station_data:
        chk = input(
            '\ndo you want to search for live timetable data for this station? (y/N)')
        if chk.lower() == "y":
            if len(station_data) > 1:
                print('multiple data points found. which one do you want to use?')
                print('-'*100)
                for i, s in enumerate(station_data):
                    print('choice: {}'.format(i))
                    print('data: {}'.format(json.dumps(
                        s, indent=2, ensure_ascii=False)))
                    print('-'*50)

                choice = input('\nchoice:_')
                station_data = station_data[int(choice)]
            else:
                station_data = station_data[0]
            search_by_station(station_CRS=station_data["CRS_main"])


if __name__ == "__main__":
    def showcase():
        describe()
        sample()
        # main()
        print('-'*100)
        print('sample record returned from CRS search: "DLY"')
        station_from_CRS(crs="DLY")
        print('-'*100)
        print('sample record returned from station name search: "Coventry"')
        station_from_name(station_name="Coventry")

    # showcase()

    CLI()
