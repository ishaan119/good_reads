from flask_nav import Nav
from flask_nav.elements import View

nav = Nav()

navitems = [
    View('Home', '.index'),
    View('Home', '.index'),
    View('Recommend a Book', '.recommend_book'),
    View('About', '.about')
]
