'''
Created on Dec 18, 2015

@author: ishaansutaria
'''

from goodreads import client
from goodreads import review
from gmaps import Geocoding
import time
import vincent
import os
import yaml
import json
import pickle
all_books_read_file = 'user_books_read.pkl'
author_hometown_file = 'author_hometown.pkl'
author_hometown_geoloc_file = 'authors_geo.pkl'

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
def getLocUsingGoogleMap(location):
    api = Geocoding()
    return api.geocode(location)


def authenticate_user():
    api_key = 'o1AEPj9ZCPOJWwgyEHImlw'
    api_secret = 'yiFxGIHVVuiZKDNlP8othONyvYISu2AH4nrMVA6Q'
    gc = client.GoodreadsClient(api_key, api_secret)
    gc.authenticate()
    return gc


def getAllBooksReadByUser(user):
    if not checkFileExists(all_books_read_file):
        k = user.review_list()
        pickle.dump(k, open(all_books_read_file, "w"))


def getHomeLocTownForAuthors(author_hometown):
    if not checkFileExists(author_hometown_geoloc_file):
        author_country = {}
        for home in author_hometown:
            if not author_hometown[home] is None:
                author_country[home] = \
                    getLocUsingGoogleMap(author_hometown[home])
        with open(author_hometown_geoloc_file, 'w') as fh:
            fh.write(json.dumps(author_country))


def checkFileExists(fileName):
    return os.path.exists(fileName)


def setup_goodreads():
    gc = authenticate_user()
    user2 = gc.user()
    getAllBooksReadByUser(user2)
    k = pickle.load(open(all_books_read_file, "r"))
    print 'All my read books'
    author_dic = {}
    for m in k:
        author_dic[m.book['authors']['author']['name']] = \
            m.book['authors']['author']['id']
    print 'Get home town for authors'
    auth_homeT = {}
    for key in author_dic:
        auth_homeT[key] = gc.author(author_dic[key]).hometown
    print auth_homeT
    getHomeLocTownForAuthors(auth_homeT)


def getCountryOfAuthors():
    setup_goodreads()
    k = pickle.load(open(all_books_read_file, "r"))
    print 'All my read books'
    author_dic = {}
    for m in k:
        author_dic[m.book['authors']['author']['name']] = \
            m.book['authors']['author']['id']
    with open(author_hometown_geoloc_file, 'r') as fh:
            author_country = yaml.safe_load(fh)
    dd = {}
    # #76
    for i in author_country:
            tmp = author_country[i][0]['formatted_address'].split(u',')[-1]
            if tmp in dd:
                dd[tmp] += 1
            else:
                dd[tmp] = 1
    bar = vincent.Bar(dd)
    bar.to_json('11', html_out=True, html_path='q.html')


def getUserFirendStatistics():
    gc = authenticate_user()
    user2 = gc.user()
    k = user2.user_firends()
    dd = {}
    freind_books = {}
    for j in k:
        dd[str(j.friend_name)] = int(j.friend_count)
        freind_books[str(j.friend_name)] = user2.review_list(page=1,
                                                             per_page=200,
                                                             shelf='read',
                                                             user_id=j.friend_id)

    print 'Average num of friends your friends have'
    print str(sum(dd.values())/len(dd.values()))
    author_dic = {}
    for tt in freind_books:
        if freind_books[tt] == [0]:
            continue
        try:
            for m in freind_books[tt]:
                author_dic[m.book['authors']['author']['name']] = \
                    m.book['authors']['author']['id']
        except:
            continue

    auth_homeT = {}
    for key in author_dic:
        auth_homeT[key] = gc.author(author_dic[key]).hometown

    getHomeLocTownForAuthors(auth_homeT)
    with open(author_hometown_geoloc_file, 'r') as fh:
            author_country = yaml.safe_load(fh)
    dd = {}
    # #76
    for i in author_country:
            tmp = author_country[i][0]['formatted_address'].split(u',')[-1]
            if tmp in dd:
                dd[tmp] += 1
            else:
                dd[tmp] = 1
    bar = vincent.Pie(dd)
    bar.legend('Country')
    bar.to_json('11', html_out=True, html_path='q.html')

getCountryOfAuthors()