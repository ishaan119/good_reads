from gmaps import Geocoding
import time
from flask import current_app


def rateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)

    def decorate(func):
        lastTimeCalled = [0.0]

        def rateLimitedFunction(*args, **kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait > 0:
                time.sleep(leftToWait)
            ret = func(*args, **kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


@rateLimited(3)
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
        return temp[0]['formatted_address'].split(u',')[-1]
    except Exception as e:
        current_app.logger.error('Exception Found for Location {0} with exception {1}'.format(location, e))
        return None

