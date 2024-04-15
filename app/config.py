import os

def getConfig():
    password = os.environ.get('password')

    config = {
        'password': password
    }
    return config
