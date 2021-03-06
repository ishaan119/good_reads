#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, render_template, flash,session,request, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from oauth import OAuthSignIn, search_books, get_book_info, analyze_user_books, get_reco_book, get_global_stats, get_gr_user_info
from flask_bootstrap import Bootstrap
from werkzeug.exceptions import HTTPException
from nav import nav, navitems
from flask_nav.elements import Navbar, View
import config
import newrelic.agent
import ast
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from utils.helper import chunks
import math
from flask_admin.contrib import sqla
from flask.ext.admin.contrib.sqla.view import func
from itertools import groupby
from sqlalchemy import func as func1
import time
app = Flask(__name__, static_url_path='/static')
config.configure_app(app)
if not app.config['ENV'] == 'dev':
    newrelic.agent.initialize('/home/ubuntu/good_reads/newrelic.ini')
Bootstrap(app)
nav.init_app(app)
db = SQLAlchemy(app)


class ModelView(ModelView):
    def is_accessible(self):
        auth = request.authorization or request.environ.get('REMOTE_USER')  # workaround for Apache
        if not auth or (auth.username, auth.password) != app.config['ADMIN_CREDENTIALS']:
            raise HTTPException('', Response(
                "Please log in.", 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            ))
        return True


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    request_token = db.Column(db.String(64), nullable=False)
    request_secret= db.Column(db.String(64), nullable=False)
    oauth_token = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(200), nullable=True)


class Invite(db.Model):
    __tablename__ = 'invite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    invite_email = db.Column(db.String(200), nullable=True)



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


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gid = db.Column(db.Integer, nullable=False, unique=True)
    isbn = db.Column(db.Integer, nullable=False, unique=True)
    isbn13 = db.Column(db.Integer, nullable=False, unique=True)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(2000), nullable=True)
    publication = db.Column(db.DateTime)
    image_url = db.Column(db.String(200), nullable=True)
    pages = db.Column(db.Integer, nullable=True)
    ratings_count = db.Column(db.DECIMAL, nullable=True)
    average_rating = db.Column(db.DECIMAL, nullable=True)
    language = db.Column(db.String, nullable=True)
    author_gid = db.Column(db.Integer, db.ForeignKey(
        'author.gid'))
    influencer_ids = db.Column(db.String(2000), nullable=False)
    user_recommended_ids = db.Column(db.String(5000), nullable=False)
    preview = db.Column(db.String(10000), nullable=True)

class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String, nullable=True)
    image_url = db.Column(db.String, nullable=True)
    books_recommended = db.Column(db.String(5000), nullable=False)
    category = db.Column(db.String(300), nullable=True)

db.create_all()

# Customized Post model admin
class AuthorAdmin(sqla.ModelView):
    column_searchable_list = ['country']
    column_editable_list = ['country']

    def get_query(self):
        return self.session.query(self.model).filter(self.model.country == None)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.country == None)

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(AuthorAdmin, self).__init__(Author, session, name='Update Author', endpoint='auth_country')


admin = Admin(app, name='Dashboard', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Author, db.session))
admin.add_view(AuthorAdmin(db.session))
admin.add_view(ModelView(Book, db.session))
admin.add_view(ModelView(Influencer, db.session))
admin.add_view(ModelView(Invite, db.session))


def user_logged_in():
    if 'user_id1' in session:
        return True
    return False


@app.route('/')
def index():
    if 'user_id1' in session:
        return redirect(url_for('user_profile'))
    app.logger.info("Index page loaded")
    register_element(nav, navitems)
    return render_template('index.html',  nav=nav.elems)


def register_element(nav1, navitems1):
    if 'user_id1' in session:
        navitems1 = (navitems1 + [View('Friends', '.get_friends')])
        navitems1 = (navitems1 + [View('Logout', '.logout')])
        navitems1 = (navitems1 + [View('Recommend A Book', '.recommend_book')])
    return nav1.register_element('top', Navbar(*navitems1))


def get_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    return user


@app.route('/profile')
def user_profile():
    register_element(nav, navitems)
    if not user_logged_in():
        return render_template('index.html', nav=nav.elems)

    user_id = session['user_id1']
    user = get_user(user_id)

    review_list, books_read, gender_analysis, fav_author, sorted_pub_year = analyze_user_books(user)
    labels = []
    values = []
    time_ss = [list(g) for k,g in groupby(sorted_pub_year, lambda i: i // 10)]
    for key in gender_analysis['ath_c']:
        labels.append(key)
        values.append(gender_analysis['ath_c'][key])

    book_reco, author_info = get_reco_book(gender_analysis)

    influencer_list = []
    influencers = Influencer.query.filter().limit(8)
    for ii in influencers:
        influencer_list.append(ii)
    app.logger.info("For user_name: {0}, Total books: {1}, Analysis: {2}".format(user.name.encode('utf-8'), len(review_list), gender_analysis))
    return render_template('starter.html', user_books=books_read, total_book=len(review_list),fav_author=fav_author,
                           gender_analysis=gender_analysis, values=values, labels=labels,
                           reco_book=book_reco, author_info=author_info, friend=False, timeline=time_ss, influencers = influencers)
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
    if 'user_id1' in session:
        session.pop('user_id1')

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
    if (isinstance(user_dict, dict) and user_dict['oauth_token'] is None) or (isinstance(user_dict, tuple) and user_dict[0] is None):
        app.logger.warning("Authentication failed")
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


@app.route('/get_friends')
def get_friends():
    register_element(nav, navitems)
    if not user_logged_in():
        return render_template('index.html', nav=nav.elems)
    user_id = session['user_id1']
    user = get_user(user_id)
    page_no = 1
    if request.args.get('page'):
        page_no = request.args.get('page')
    oauth = OAuthSignIn.get_provider('goodreads')
    user_friends, total_friends = oauth.get_user_friends(user.request_token, user.request_secret, user_id, page_no)

    f_list = []
    for fr in user_friends:
        tt_dic = {}
        tt_dic['name'] = fr.friend_name
        tt_dic['image_url'] = fr.image
        tt_dic['friend_id'] = fr.friend_id
        f_list.append(tt_dic)
    chunk_f_list = list(chunks(f_list, 4))
    total_pages = int(math.ceil(float(total_friends)/30.0))
    app.logger.info("For username:{0}, loaded friends page: {1}, with total friends: {2}".format(user.name.encode('utf-8'), page_no, total_friends))
    return render_template('friend_list.html', nav=nav.elems, friends=chunk_f_list, pages=total_pages)

@app.route('/get_friends_info')
def get_friends_info():
    register_element(nav, navitems)
    if not user_logged_in():
        return render_template('index.html', nav=nav.elems)
    user_id = session['user_id1']
    user = get_user(user_id)
    page_no = 1
    if request.args.get('page'):
        page_no = request.args.get('page')
    oauth = OAuthSignIn.get_provider('goodreads')
    user_friends, total_friends = oauth.get_user_friends(user.request_token, user.request_secret, user_id, page_no)

    f_list = []
    for fr in user_friends:
        tt_dic = {}
        tt_dic['name'] = fr.friend_name
        tt_dic['image_url'] = fr.image
        tt_dic['friend_id'] = fr.friend_id
        f_list.append(tt_dic)
    return jsonify(f_list)



@app.route('/get_friend_stats', methods=['GET', 'POST'])
def get_friend_stats():
    register_element(nav, navitems)
    if not user_logged_in():
        return render_template('index.html', nav=nav.elems)
    user_id = session['user_id1']
    user = get_user(user_id)
    friend = ast.literal_eval(request.form['friend'])

    review_list, books_read, gender_analysis, fav_author, sorted_pub_year = analyze_user_books(user, friend['friend_id'])
    labels = []
    values = []
    time_ss = [list(g) for k, g in groupby(sorted_pub_year, lambda i: i // 10)]
    for key in gender_analysis['ath_c']:
        labels.append(key)
        values.append(gender_analysis['ath_c'][key])

    book_reco, author_info = get_reco_book(gender_analysis)
    app.logger.info(
        "For user_name: {0}, Total books: {1}, Analysis: {2}".format(user.name.encode('utf-8'), len(review_list), gender_analysis))
    return render_template('starter.html', user_books=books_read, total_book=len(review_list),
                           gender_analysis=gender_analysis, values=values, labels=labels,
                           reco_book=book_reco, author_info=author_info, friend=True, finfo=friend, fav_author=fav_author, timeline=time_ss)


@app.route('/recommend/book/', methods=['GET','POST'])
def recommend_book():
    if request.method == "POST":
        app.logger.info("Book recommendations search")
        books = search_books(request.form['search'])
        return render_template('recommend_book.html', nav=nav.elems, books=books, reco_successful=False)
    else:
        app.logger.info("Book recommendations page loaded")
        register_element(nav, navitems)
        return render_template('recommend_book.html', nav=nav.elems, reco_successful=False)


@app.route('/about')
def about():
    app.logger.info("About Page loaded")
    register_element(nav, navitems)
    return render_template('about.html', nav=nav.elems)


@app.route('/user/info', methods=['GET'])
def get_user_info():
    if not user_logged_in():
        return render_template('index.html', nav=nav.elems)
    user_id = session['user_id1']
    user = get_user(user_id)
    info = get_gr_user_info(user.user_id, user.request_token, user.request_secret)

    return jsonify({"name": info.name, "image_url": info.small_image_url, "email": user.email})


@app.route('/recommendations', methods=['GET', 'POST'])
def add_recommended_book():
    app.logger.info("Book recommendations added")
    book_id = request.form['reco']
    get_book_info(book_id)
    register_element(nav, navitems)
    return render_template('recommend_book.html', nav=nav.elems, reco_successful=True)


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    register_element(nav, navitems)
    if request.method == "POST":
        app.logger.info("Name: {0}, Email: {1}, Message:{2}".format(request.form['Name'],
                                                                    request.form['email'],
                                                                    request.form['Message']))
        return render_template('feedback.html', nav=nav.elems, feedback_successful=True)
    else:
        return render_template('feedback.html', nav=nav.elems, feedback_successful=False)


@app.route('/global_stats', methods=['GET'])
def calc_global_stats():
    get_global_stats()
    return "", 200


@app.route('/influencers', methods=['GET','POST'])
def get_influencers():
    register_element(nav, navitems)
    influencer_name = Influencer.query.distinct(Influencer.name)
    temp = []
    for name in influencer_name:
        temp.append(name.name)
    return render_template('influencers.html',influencers=influencer_name,nav=nav.elems)


@app.route('/influencer_recommendations', methods=['GET','POST'])
def influencer_reco():
    register_element(nav, navitems)
    influencer_name = Influencer.query.filter_by(name=str(request.args["influencer_name"]).strip()).first()
    books = search_books(request.args["book_name"])
    return render_template('influencer_recommendation.html', influencers=influencer_name,nav=nav.elems, books=books, reco_successful=False)


@app.route('/add_influencer_recommendation', methods=['POST'])
def add_influencer_recommendation():
    register_element(nav, navitems)
    book_id, influencer_id = str(request.form['reco']).split('+')
    book_id = book_id.strip()
    influencer_id = influencer_id.strip()
    book_data = get_book_info(book_id)
    if book_data is None:
        return render_template('influencers.html', influencers=[], nav=nav.elems)
    influencer_list = ast.literal_eval(book_data.influencer_ids)
    if influencer_id not in influencer_list:
        influencer_list.append(influencer_id)
    Book.query.filter_by(gid=book_id).update({'influencer_ids':str(influencer_list)})
    influencer_data = Influencer.query.filter_by(id=influencer_id).first()
    influencer_books = ast.literal_eval(influencer_data.books_recommended)
    if book_id not in influencer_books:
        influencer_books.append(book_id)
    Influencer.query.filter_by(id=influencer_id).update({'books_recommended': str(influencer_books)})
    db.session.commit()
    influencer_name = Influencer.query.distinct(Influencer.name)
    temp = []
    for name in influencer_name:
        temp.append(name.name)
    return render_template('influencers.html', influencers=influencer_name, nav=nav.elems)


@app.route('/book_recommendation_influencer', methods=['GET'])
def book_recommendation_influencer():
    register_element(nav, navitems)
    page = request.args.get('page', 1, type=int)
    influencers = Influencer.query.order_by(Influencer.id.asc()).paginate(
        page, 8, False)
    next_url = url_for('book_recommendation_influencer', page=influencers.next_num) if influencers.has_next else None
    prev_url = url_for('book_recommendation_influencer', page=influencers.prev_num) if influencers.has_prev else None
    return render_template('book_recommendation.html', next_url=next_url, prev_url=prev_url,influencers=influencers.items, nav=nav.elems)


@app.route('/user', methods=['GET', 'PUT'])
def get_update_user():
    print("Adding user email")
    user_id = session['user_id1']
    User.query.filter_by(user_id=user_id).update({'email': str(request.form['EMAIL'])})
    db.session.commit()
    return jsonify({"msg":"success"})

@app.route('/individual_influencer_reco', methods=['GET'])
def individual_influencer_reco():
    influencer_id = request.args.get('influencer_id')
    influencer_data = Influencer.query.filter_by(id=influencer_id).first()
    books = ast.literal_eval(influencer_data.books_recommended)
    recommended_list = []
    for book_id in books:
        temp = Book.query.filter_by(gid=book_id).first()
        recommended_list.append(temp)
    return render_template('influencers_book.html', book_list=recommended_list,name=influencer_data.name, image_url=influencer_data.image_url,
                           nav=nav.elems, description=influencer_data.description)

@app.route('/invite_friends', methods=['POST',])
def invite_friends():
    email =  request.form['Email']
    user_id = session['user_id1']
    invite_data = Invite(user_id=user_id, invite_email=email)
    try:
        db.session.add(invite_data)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return jsonify({"msg": "success"})


@app.route('/explore', methods=['GET'])
def explore_authors():
    print "Explore called"
    book_preview = Book.query.filter(Book.preview != None).order_by(func1.random()).first()
    text = book_preview.preview
    return render_template('explore.html', book_text=text, book_name=book_preview.title, book_image_url=book_preview.image_url)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'],host='0.0.0.0')
