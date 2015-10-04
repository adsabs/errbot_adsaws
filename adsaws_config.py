# encoding: utf-8
"""
Configuration file for the ADSAWS services
"""

AWS_REGION = 'region'
AWS_ACCESS_KEY = 'key'
AWS_SECRET_KEY = 'secret'

try:
    from local_config import *
except:
    pass