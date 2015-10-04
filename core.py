# encoding: utf-8

import adsaws_config

from boto3.session import Session

def get_boto3_session():
    """
    Gets a boto3 session using credentials stores in app.config; assumes an
    app context is active
    :return: boto3.session instance
    """
    return Session(
        aws_access_key_id=adsaws_config.AWS_ACCESS_KEY,
        aws_secret_access_key=adsaws_config.AWS_SECRET_KEY,
        region_name=adsaws_config.AWS_REGION
    )
