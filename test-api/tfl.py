import requests
import json
from collections import defaultdict


def get_severity_list(show_json=True):
    url = "https://api.tfl.gov.uk/Line/Meta/Severity?app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519"
    r = requests.get(url).json()

    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    all_modes = list(set([m["modeName"] for m in r]))

    # group by transport mode
    temp_dict = defaultdict.fromkeys(all_modes)
    severity_dict = {}
    for k in temp_dict.keys():
        severity_dict[k] = []

    for mode in r:
        severity_dict[mode["modeName"]].append({
            "level": mode["severityLevel"],
            "description": mode["description"]
        })

    with open('tfl-severity-modes.json', "w") as f:
        json.dump(severity_dict, f, indent=4, ensure_ascii=False)

    return severity_dict


def all_modes_of_transport(show_json=True):
    url = "https://api.tfl.gov.uk/Line/Meta/Modes?app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519"
    r = requests.get(url).json()

    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    with open('tfl-modes.json', "w") as f:
        json.dump(r, f, indent=4, ensure_ascii=False)

    return r


def all_lines_and_routes(line_type=None, show_json=True):
    """
    Gets all lines and their valid routes for given modes, including the name and id of the originating and terminating stops for each route
    """
    train_types = ["dlr", "national-rail",
                   "overground", "tflrail", "tram", "tube"]

    if line_type:
        modes_to_search = line_type
    else:
        modes_to_search = train_types

    if not type(modes_to_search) == list:
        url = "https://api.tfl.gov.uk/Line/Mode/{}/Route?serviceTypes=Regular&app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519".format(
            modes_to_search)
    else:
        modes_str = '%2C%20'.join(modes_to_search)
        url = "https://api.tfl.gov.uk/Line/Mode/{}/Route?serviceTypes=Regular&app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519".format(
            modes_str)

    print(url)
    r = requests.get(url).json()

    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    with open('tfl-all-lines.json', "w") as f:
        json.dump(r, f, indent=4, ensure_ascii=False)

    return r


# might not be correct
def check_for_line_disruption(show_json=True, from_file=True):
    if from_file:
        filepath = "./providers/tfl/tfl-all-lines.json"

        with open(filepath) as f:
            all_lines = json.load(f)
    else:
        all_lines = all_lines_and_routes(show_json=False)

    modes = set([l["modeName"] for l in all_lines])

    output = []
    for line in all_lines:
        if len(line["disruptions"]) > 1:
            output.append(line)

    if show_json:

        if len(output) == 0:
            print(
                '\nno disruptions on the following modes of transport: {}'.format(modes))
        else:
            print('\ndisruptions on lines: ')
            for o in output:
                print(json.dumps(o, indent=4, ensure_ascii=False))

    return output


def check_status_of_all_lines(modes="national-rail", show_disruption_only=False, show_json=True, raw=False):
    # https://api.tfl.gov.uk/swagger/ui/index.html?url=/swagger/docs/v1#!/Line/Line_StatusByMode

    def filter_status(mode="national-rail"):
        ok_codes = {
            "national-rail": [10, 18, 19],
            "tflrail": [10, 18, 19],
            "overground": [10, 18, 19],
            "dlr": [10, 18, 19],
            "tram": [10, 18, 19],
            "tube": [10, 18, 19]
        }

        try:
            ok_codes[mode]
        except:
            raise SystemExit('error codes not found. cannot filter.')

        status_list = []
        if mode['modeName'] == mode:
            for status in mode["lineStatuses"]:
                # print('checking {} against {}'.format(status["statusSeverity"], national_rail_codes))
                if not int(status["statusSeverity"]) in ok_codes[mode]:
                    status_list.append({
                        "severity": status["statusSeverity"],
                        "description": status["statusSeverityDescription"]
                    })
                else:
                    continue
        return status_list

    if type(modes) == list:
        modes_to_check = "%2C%20".join(modes)
    else:
        modes_to_check = modes
    url = "https://api.tfl.gov.uk/Line/Mode/{}/Status?detail=true&app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519".format(
        modes_to_check)
    r = requests.get(url).json()

    if show_json:
        pass
        # print(json.dumps(r, indent=4, ensure_ascii=False))

    if not raw:
        output = []
        for mode in r:
            if show_disruption_only:
                # national-rail == all except code 10, 18, 19
                status_list = filter_status(mode=modes)

                if len(status_list) > 0:
                    output.append({
                        "id": mode['id'],
                        "severity": status_list
                    })

            else:
                # show all statuses
                status_list = []
                for status in mode["lineStatuses"]:
                    status_list.append({
                        "severity": status["statusSeverity"],
                        "description": status["statusSeverityDescription"]
                    })

                output.append({
                    "id": mode['id'],
                    "severity": status_list,
                })

        if show_json:
            [print(o) for o in output]

        return output
    else:
        return r


def check_for_station_disruption(show_json=True):
    # ref: https://api.tfl.gov.uk/swagger/ui/index.html?url=/swagger/docs/v1#!/StopPoint/StopPoint_DisruptionByMode
    # maybe more detailed: https://api.tfl.gov.uk/swagger/ui/index.html?url=/swagger/docs/v1#!/StopPoint/StopPoint_Disruption
    url = "https://api.tfl.gov.uk/StopPoint/Mode/national-rail/Disruption?includeRouteBlockedStops=true&app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519"
    r = requests.get(url).json()

    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    return r


def station_by_name(station_name="st albans", show_json=True):
    station_name = station_name.replace(' ', "%20")
    url = "https://api.tfl.gov.uk/StopPoint/Search/{}?app_key=9f418ee21efced9b919d6da9bef9f88b&app_id=03a0c519".format(
        station_name)
    r = requests.get(url).json()

    if show_json:
        print(json.dumps(r, indent=4, ensure_ascii=False))

    return r


def describe():
    print('extra info')
    crowd_url = "https://api.tfl.gov.uk/swagger/ui/index.html?url=/swagger/docs/v1#!/StopPoint/StopPoint_Crowding"
    print('crowdedness data: {}'.format(crowd_url))


if __name__ == "__main__":
    # all_modes_of_transport()
    # all_lines_and_routes()
    # check_for_disruption()
    # get_severity_list()

    check_status_of_all_lines(modes="national-rail", show_disruption_only=True)
    # check_for_station_disruption()
    # station_by_name()
