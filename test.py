'''
Created on Dec 17, 2015

@author: ishaansutaria
'''
from goodreads import client
from gmaps import Geocoding
import time
import vincent


def RateLimited(maxPerSecond):
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


@RateLimited(3)
def getLocUsingGMaps(location):
    api = Geocoding()
    return api.geocode(location)

api_key = 'o1AEPj9ZCPOJWwgyEHImlw'
api_secret = 'yiFxGIHVVuiZKDNlP8othONyvYISu2AH4nrMVA6Q'
gc = client.GoodreadsClient(api_key, api_secret)
gc.authenticate()
user2 = gc.user()
k = user2.review_list()
print 'All my read books'
author_dic = {}
sum = 0
for m in k:
    sum += 1
    author_dic[m.book['authors']['author']['name']] = \
        m.book['authors']['author']['id']
print 'Total number of books: ' + str(sum)
print 'Get hometown for authors'
author_hometown = {}
for key in author_dic:
    author_hometown[key] = gc.author(author_dic[key]).hometown

author_country = {}
dd = {}
sum1 = 0
for home in author_hometown:
    if author_hometown[home] is not None:
        author_country[home] = getLocUsingGMaps(author_hometown[home])
    else:
        sum1 += 1
print 'Total books with none: ' + str(sum1)
print len(author_country.keys())
for i in author_country:
    temp = author_country[i][0]['formatted_address'].split(u',')[-1]
    if temp in dd:
        dd[temp] += 1
    else:
        dd[temp] = 1

print len(dd.keys())
bar = vincent.Bar(dd)
bar.to_json('11', html_out=True, html_path='ww.html')
#for key in dd:
#    print str(key) + ':' + str(dd[key])