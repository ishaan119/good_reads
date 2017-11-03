from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session
import xmltodict
from goodreads.author import GoodreadsAuthor
from data.models import Author, db
from datetime import datetime
from utils.helper import get_author_country
from goodreads.friend import GoodreadFriend

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
        #return url_for('oauth_callback', provider=self.provider_name,
        #               _external=True)
        callback_url = "http://recommendmebooks.com/callback/goodreads"
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
            request_token_url='http://www.goodreads.com/oauth/request_token',
            authorize_url='http://www.goodreads.com/oauth/authorize',
            access_token_url='http://www.goodreads.com/oauth/access_token',
            base_url='http://www.goodreads.com/'
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
        request_token = session.pop('request_token')
        if 'oauth_token' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            request_token[0],
            request_token[1],
            data={'oauth_token': request.args['oauth_token']}
        )
        print oauth_session.access_token_secret
        print oauth_session.access_token
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
        me = oauth_session.get('/review/list.xml', params={'v': '2', 'id': user_id, 'page': '1',
                                                      'shelf': 'read', 'per_page': 200})
        return xmltodict.parse(me.content)

    def get_author_info(self, author_id, request_token, request_secret):
        author_data = Author.query.filter_by(gid=author_id).first()
        if not author_data:
            oauth_session = self.service.get_session(
                (request_token,
                 request_secret)
            )
            me = oauth_session.get('/author/show.xml', params={'id': author_id})
            r = GoodreadsAuthor(xmltodict.parse(me.content)['GoodreadsResponse']['author'])
            country = get_author_country(r.hometown)
            author_data = Author(gid=r.gid, name=r.name, about=r.about, born_at=r.born_at,
                                 died_at=r.died_at, fans_count=r.fans_count, gender=r.gender,
                                 hometown=r.hometown, works_count=r.works_count, image_url=r.image_url,
                                 country=country, books=r.books)
            db.session.add(author_data)
            db.session.commit()
            author_data = Author.query.filter_by(gid=author_id).first()
            return author_data
        else:
            return author_data

    def get_user_friends(self,request_token, request_secret, user_id):
        oauth_session = self.service.get_session(
            (request_token,
             request_secret)
        )
        me = oauth_session.get('/friend/user.xml', params={'id': user_id})
        friends = [friend.GoodreadFriend(user)
         for user in resp['friends']['user']]
        friends = GoodreadFriend(xmltodict.parse(me.content)['GoodreadsResponse']['friends'])
        print friends
