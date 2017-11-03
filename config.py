import os
import os
import logging


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_LOCATION = 'oorjan.log'
    LOGGING_LEVEL = logging.DEBUG
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'mysql://root:1111@localhost/SOLAR_DATA'


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


config = {
    "development": "app.config.DevelopmentConfig",
    "testing": "app.config.TestingConfig",
    "default": "app.config.DevelopmentConfig",
    "production": "app.config.ProductionConfig"
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION1', 'development')
    print config_name
    app.config.from_object(config[config_name])
    # app.config.from_envvar('FLASK_CONFIG')
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_LOCATION = 'gr.log'
    LOGGING_LEVEL = logging.DEBUG

    # Configure logging
    handler = logging.FileHandler(LOGGING_LOCATION)
    handler.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter(LOGGING_FORMAT)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)