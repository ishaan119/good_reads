from gmaps import Geocoding
import time
from flask import current_app


def __get_loc_using_gmaps(location):
    api = Geocoding(api_key=current_app.config['GOOGLE_GEO_CODE_API_KEY'])
    return api.geocode(location)


def get_author_country(location):
    if location is None:
        current_app.logger.info("Location is non")
        return None
    try:
        location = location.encode("utf-8")
        temp = __get_loc_using_gmaps(location)
        print temp
        return temp[0]['formatted_address'].split(u',')[-1].strip()
    except Exception as e:
        current_app.logger.error('Exception Found for Location {0} with exception {1}'.format(location, e))
        return None


# Create a function called "chunks" with two arguments, l and n:
def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]