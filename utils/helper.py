from gmaps import Geocoding


def __get_loc_using_gmaps(location):
    api = Geocoding()
    return api.geocode(location)


def get_author_country(location):
    if location is None:
        return None
    try:
        temp = __get_loc_using_gmaps(location)
        print temp
        return temp[0]['formatted_address'].split(u',')[-1]
    except:
        print 'Exception Found for Location'
        return None
