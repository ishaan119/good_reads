from flask import Flask, redirect, url_for, render_template, flash,session,jsonify
from flask_sqlalchemy import SQLAlchemy
from oauth import OAuthSignIn
from flask_bootstrap import Bootstrap
from nav import nav
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION


app = Flask(__name__)
Bootstrap(app)
nav.init_app(app)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': 'xx',
        'secret': 'xx'
    },
    'goodreads': {
        'id': 'AiavlqI7ZR55oBzDbT1y2w',
        'secret': 'nyxzFDTt63e8f9SjgXlBOIQylq2eNqrRszbS2TiDzA'
    }
}
book_author = {}
db = SQLAlchemy(app)


class User( db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    request_token = db.Column(db.String(64), nullable=False)
    request_secret= db.Column(db.String(64), nullable=False)
    oauth_token = db.Column(db.String(64), nullable=False)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    about = db.Column(db.String(1000), nullable=True)
    born_at = db.Column(db.DateTime)
    died_at = db.Column(db.DateTime)
    fans_count = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    hometown=db.Column(db.String(120), nullable=True)
    works_count = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    books = db.Column(db.String(200), nullable=True)

print("asda")
# Initializing flask navbar
nav.register_element('frontend_top', Navbar(
    View('Flask-Bootstrap', '.index'),
    View('Home', '.index'),
    View('Forms Example', '.analyze_books_read'),
    Subgroup(
        'Docs',
        Link('Flask-Bootstrap', 'http://pythonhosted.org/Flask-Bootstrap'),
        Link('Flask-AppConfig', 'https://github.com/mbr/flask-appconfig'),
        Link('Flask-Debug', 'https://github.com/mbr/flask-debug'),
        Separator(),
        Text('Bootstrap'),
        Link('Getting started', 'http://getbootstrap.com/getting-started/'),
        Link('CSS', 'http://getbootstrap.com/css/'),
        Link('Components', 'http://getbootstrap.com/components/'),
        Link('Javascript', 'http://getbootstrap.com/javascript/'),
        Link('Customize', 'http://getbootstrap.com/customize/'), )))


@app.route('/')
def index():
    return render_template('index.html')

def get_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    return user


@app.route('/profile')
def user_profile():
    user_id = session['user_id1']
    user = get_user(user_id)
    oauth = OAuthSignIn.get_provider('goodreads')
    user_books = oauth.get_user_books(user.request_token,user.request_secret,user.oauth_token,user.user_id)
    review_list = user_books['GoodreadsResponse']['reviews']['review']
    books_read = {}
    for review in review_list:
        book_author[review['book']['authors']['author']['name']] = review['book']['authors']['author']['id']
        if review['book']['authors']['author']['name'] in books_read:
            books_read[review['book']['authors']['author']['name']].append(review['book']['title'])
        else:
            books_read[review['book']['authors']['author']['name']] = [review['book']['title']]

    authors = []
    gender_analysis = {'male': 0, 'female': 0, 'ath_c': {}}
    for author_name in book_author:
        author_info = oauth.get_author_info(book_author[author_name], user.request_token, user.request_secret)
        if author_info.gender == 'male':
            gender_analysis['male'] += 1
        else:
            gender_analysis['female'] += 1
        if author_info.country in gender_analysis['ath_c']:
            gender_analysis['ath_c'][author_info.country] += 1
        else:
            gender_analysis['ath_c'][author_info.country] = 1

    labels = []
    values = []
    for key in gender_analysis['ath_c']:
        labels.append(key)
        values.append(gender_analysis['ath_c'][key])

    return render_template('profile.html', user_books=books_read, total_book=len(review_list),
                           gender_analysis=gender_analysis, values=values, labels=labels)
    # return jsonify(user_books)


@app.route('/analyze/books_read/gender_distribution')
def gender_distribution():
    user_id = session['user_id1']
    analysis = session['analysis']
    labels = ["Male", "Female"]
    values = [analysis['male'], analysis['female']]
    return render_template('bar_chart.html', values=values, labels=labels)


@app.route('/analyze/books_read/country_distribution')
def country_distribution():
    user_id = session['user_id1']
    analysis = session['analysis']
    labels = []
    values = []
    for key in analysis['ath_c']:
        labels.append(key)
        values.append(analysis['ath_c'][key])
    return render_template('bar_chart.html', values=values, labels=labels)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize


@app.route('/analyze/books_read/')
def analyze_books_read():
    user_id = session['user_id1']
    user = get_user(user_id)
    oauth = OAuthSignIn.get_provider('goodreads')
    authors = []
    gender_analysis = {'male': 0, 'female': 0, 'ath_c': {}}
    for author_name in book_author:
        author_info = oauth.get_author_info(book_author[author_name], user.request_token, user.request_secret)
        if author_info.gender == 'male':
            gender_analysis['male'] += 1
        else:
            gender_analysis['female'] += 1
        if author_info.country in gender_analysis['ath_c']:
            gender_analysis['ath_c'][author_info.country] += 1
        else:
            gender_analysis['ath_c'][author_info.country] = 1
    session['analysis'] = gender_analysis
    return render_template('analyze_author.html')


@app.route('/callback/<provider>')
def oauth_callback(provider):
    oauth = OAuthSignIn.get_provider(provider)
    user_dict = oauth.callback()
    print user_dict
    if 'as' is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    gr_response = user_dict['user_info']['GoodreadsResponse']['user']
    user = User.query.filter_by(user_id=gr_response['@id']).first()
    if not user:
        user = User(user_id=gr_response['@id'], name=gr_response['name'],
                    request_token=user_dict['request_token'], request_secret=user_dict['request_secret'],
                    oauth_token=user_dict['oauth_token'])
        db.session.add(user)
        db.session.commit()
    session['user_id1'] = gr_response['@id']
    return redirect(url_for('user_profile'))


@app.route('/get_friend/stats')
def get_friend_stats():
    user_id = session['user_id1']
    user = get_user(user_id)
    oauth = OAuthSignIn.get_provider('goodreads')
    user_friends = oauth.get_user_friends(user.request_token, user.request_secret, user_id)
    print user_friends

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True,host='0.0.0.0')
