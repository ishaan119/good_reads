from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
