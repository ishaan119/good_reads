from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session
import xmltodict
from goodreads.author import GoodreadsAuthor
from goodreads.book import GoodreadsBook
from data.models import Author, db, Book
from utils.helper import get_author_country
from goodreads.friend import GoodreadFriend
import requests
import collections


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        if current_app.config['ENV'] == "dev":
            return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)
        else:
            callback_url = current_app.config['CALLBACK']
        return callback_url


    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()}
        )
        me = oauth_session.get('me?fields=id,email').json()
        return (
            'facebook$' + me['id'],
            me.get('email').split('@')[0],  # Facebook does not provide
                                            # username, so the email's user
                                            # is used instead
            me.get('email')
        )


class GoodReadsSignIn(OAuthSignIn):
    def __init__(self):
        super(GoodReadsSignIn, self).__init__('goodreads')
        self.service = OAuth1Service(
            name='goodreads',
            consumer_key=self.consumer_id,
            consumer_secret=self.consumer_secret,
            request_token_url='https://www.goodreads.com/oauth/request_token',
            authorize_url='https://www.goodreads.com/oauth/authorize',
            access_token_url='https://www.goodreads.com/oauth/access_token',
            base_url='https://www.goodreads.com/'
        )

    @property
    def authorize(self):
        request_token = self.service.get_request_token(
            params={'oauth_callback': self.get_callback_url()}
        )
        session['request_token'] = request_token
        print self.service.get_authorize_url(request_token[0])
        dict_callback = {'oauth_callback': self.get_callback_url()}
        return redirect(self.service.get_authorize_url(request_token[0], oauth_callback=self.get_callback_url()))

    def callback(self):
        if 'request_token' not in session:
            current_app.logger.error("Error validating oauth")
            return None
        request_token = session.pop('request_token')
        if 'oauth_token' not in request.args or request.args['authorize'] == '0':
            current_app.logger.info("Oauth failed")
            return None, None, None
        oauth_session = self.service.get_auth_session(
            request_token[0],
            request_token[1],
            data={'oauth_token': request.args['oauth_token']}
        )
        me = oauth_session.get('api/auth_user')
        user_info = xmltodict.parse(me.content)
        user = {'request_token':oauth_session.access_token,'request_secret':oauth_session.access_token_secret,
                     'oauth_token':request.args['oauth_token'],'user_info': user_info}
        return user

    def get_user_books(self, request_token, request_secret, oauth_token,user_id):
        oauth_session = self.service.get_session(
            (request_token,
             request_secret)
        )
        page = 1
        me = oauth_session.get('/review/list.xml', params={'v': '2', 'id': user_id, 'page': page,
                                                      'shelf': 'read', 'per_page': 200})
        content = xmltodict.parse(me.content)
        total_books = int(content['GoodreadsResponse']['reviews']['@total'])
        current_books_at = int(content['GoodreadsResponse']['reviews']['@end'])
        while total_books > current_books_at:
            page += 1
            me = oauth_session.get('/review/list.xml', params={'v': '2', 'id': user_id, 'page': page,
                                                               'shelf': 'read', 'per_page': 200})
            cc = xmltodict.parse(me.content)
            content['GoodreadsResponse']['reviews']['review'].extend(cc['GoodreadsResponse']['reviews']['review'])
            current_books_at = int(cc['GoodreadsResponse']['reviews']['@end'])
        return content

    def get_user_friends(self,request_token, request_secret, user_id, page=1):
        oauth_session = self.service.get_session(
            (request_token,
             request_secret)
        )
        me = oauth_session.get('/friend/user.xml', params={'id': user_id, 'page': page})
        friends = xmltodict.parse(me.content)['GoodreadsResponse']
        total_friends = friends['friends']['@total']
        friend_data = [GoodreadFriend(user) for user in friends['friends']['user']]
        return friend_data, total_friends


def search_books(q, page=1, search_field='all'):
    resp = requests.get("https://www.goodreads.com/search/index.xml",
                            {'key':current_app.config['OAUTH_CREDENTIALS']['goodreads']['id'],
                             'q': q, 'page': page, 'search[field]': search_field})
    content = xmltodict.parse(resp.content)['GoodreadsResponse']
    works = content['search']['results']['work']
    # If there's only one work returned, put it in a list.
    if type(works) == collections.OrderedDict:
        works = [works]
    search_results = []
    for work in works[0:3]:
        tt = {}
        tt['author'] = work['best_book']['author']['name']
        tt['author_id'] = work['best_book']['author']['id']['#text']
        tt['book_id'] = work['best_book']['id']['#text']
        tt['title'] = work['best_book']['title']
        tt['image'] = work['best_book']['image_url']
        search_results.append(tt)
    return search_results


def get_reco_book():
    book_data = Book.query.first()
    author_info = Author.query.filter_by(gid=book_data.author_gid)
    return [book_data, author_info]


def get_book_info(book_id):
    """Get info about a book"""
    book_data = Book.query.filter_by(gid=book_id).first()
    if not book_data:
        resp = requests.get("https://www.goodreads.com/book/show", {'id': book_id,
                                                                    'key':current_app.config['OAUTH_CREDENTIALS']['goodreads']['id']})
        r = GoodreadsBook(xmltodict.parse(resp.content)['GoodreadsResponse']['book'])
        author_data = get_author_info(r.authors[0].gid)
        book_data = Book(gid=r.gid, isbn=r.isbn, isbn13=r.isbn13, title=r.title,
                           description= r.description, publication=r.publication_date,
                           image_url=r.image_url, pages=r.num_pages, ratings_count=r.ratings_count,
                           average_rating=r.average_rating, language=r.language_code, author_gid=author_data.gid)
        try:
            db.session.add(book_data)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error("Error while commiting to DB with err: {0}".format(e))
        book_data = Book.query.filter_by(gid=book_id).first()
        return book_data
    else:
        return book_data


def get_author_info(author_id):
    author_data = Author.query.filter_by(gid=author_id).first()
    if not author_data:
        me = requests.get('https://www.goodreads.com/author/show.xml', params={'id': author_id,
                                                                               'key': current_app.config['OAUTH_CREDENTIALS']['goodreads']['id']})
        r = GoodreadsAuthor(xmltodict.parse(me.content)['GoodreadsResponse']['author'])
        country = get_author_country(r.hometown)
        author_data = Author(gid=r.gid, name=r.name, about=r.about, born_at=r.born_at,
                             died_at=r.died_at, fans_count=r.fans_count, gender=r.gender,
                             hometown=r.hometown, works_count=r.works_count, image_url=r.image_url,
                             country=country, books=r.books)
        try:
            db.session.add(author_data)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error("Error while commiting to DB with err: {0}".format(e))
        author_data = Author.query.filter_by(gid=author_id).first()
        return author_data
    else:
        return author_data


def analyze_user_books(user, friend_id=None):
    oauth = OAuthSignIn.get_provider('goodreads')
    if friend_id is not None:
        user_id = friend_id
    else:
        user_id = user.user_id
    user_books = oauth.get_user_books(user.request_token, user.request_secret, user.oauth_token, user_id)
    books_read = {}
    book_author = {}
    review_list = []
    books_published_timeline = []
    if 'review' in user_books['GoodreadsResponse']['reviews']:
        review_list = user_books['GoodreadsResponse']['reviews']['review']
        if type(review_list) is not list:
            review_list = [review_list]
        for review in review_list:
            temp = {}
            book_author[review['book']['authors']['author']['name']] = review['book']['authors']['author']['id']
            book_data = GoodreadsBook(review['book'])
            if book_data.publication_date is not None:
                books_published_timeline.append(book_data.publication_date.year)
            if review['book']['authors']['author']['name'] in books_read:
                books_read[review['book']['authors']['author']['name']].append(review['book']['title'])
            else:
                books_read[review['book']['authors']['author']['name']] = [review['book']['title']]
    else:
        current_app.logger.info("No books found for the user_id: " + user.name)
    gender_analysis = {'male': 0, 'female': 0, 'ath_c': {}}
    for author_name in book_author:
        author_info = get_author_info(book_author[author_name])
        if author_info is None:
            continue
        if author_info.gender == 'male':
            gender_analysis['male'] += 1
        else:
            gender_analysis['female'] += 1
        if author_info.country in gender_analysis['ath_c']:
            gender_analysis['ath_c'][author_info.country] += 1
        else:
            gender_analysis['ath_c'][author_info.country] = 1

    # Get favorite auhtor
    most_books_read_count = 0
    fav_author = ''
    for author, books in books_read.items():
        if len(books) > most_books_read_count:
            most_books_read_count = len(books)
            fav_author = author
    return review_list, books_read, gender_analysis, fav_author, sorted(books_published_timeline)
