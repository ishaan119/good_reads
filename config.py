import os
import os
from logging.handlers import RotatingFileHandler
import logging


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'top secret!'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
    OAUTH_CREDENTIALS = {
        'facebook': {
            'id': 'xx',
            'secret': 'xx'
        },
        'goodreads': {
            'id': 'AiavlqI7ZR55oBzDbT1y2w',
            'secret': 'nyxzFDTt63e8f9SjgXlBOIQylq2eNqrRszbS2TiDzA'
        }
    }
    CALLBACK = "http://localhost:5000/callback/goodreads"
    ENV = "dev"
    LOG_LEVEL = 10
    GOOGLE_GEO_CODE_API_KEY = os.getenv("GOOGLE_GEO_CODE_API_KEY")


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'top secret!'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
    OAUTH_CREDENTIALS = {
        'facebook': {
            'id': 'xx',
            'secret': 'xx'
        },
        'goodreads': {
            'id': 'AiavlqI7ZR55oBzDbT1y2w',
            'secret': 'nyxzFDTt63e8f9SjgXlBOIQylq2eNqrRszbS2TiDzA'
        }
    }
    CALLBACK = "http://recommendmebooks.com/callback/goodreads"
    ENV = 'prod'
    LOG_LEVEL = 20
    GOOGLE_GEO_CODE_API_KEY = os.getenv("GOOGLE_GEO_CODE_API_KEY")


config = {
    "development": "app.config.DevelopmentConfig",
    "testing": "app.config.TestingConfig",
    "default": "app.config.DevelopmentConfig",
    "production": "app.config.ProductionConfig"
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'development')
    app.config.from_object(config[config_name])
    # app.config.from_envvar('FLASK_CONFIG')

    handler = RotatingFileHandler('rcm.log', maxBytes=1000000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config['LOG_LEVEL'])
