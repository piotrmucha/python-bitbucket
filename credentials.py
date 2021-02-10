from dataclasses import dataclass
import configparser
from pathlib import Path


@dataclass
class BitbucketCredentials:
    username: str
    appkey: str


def get_credentials_for_bitbucket(credentials: str = f'{Path.home()}/bitbucket-credentials') -> BitbucketCredentials:
    config = configparser.RawConfigParser()
    config.read(credentials)
    try:
        details_dict = dict(config.items('CREDENTIALS'))
    except configparser.NoSectionError:
        print(f"Can't find {credentials} file with section CREDENTIALS.")
        exit(1)
    username = details_dict.get('username')
    appkey = details_dict.get('appkey')
    if username is None:
        print(f"Can't find username in {credentials} file ")

    if appkey is None:
        print(f"Can't find appkey in {credentials} file ")
    return BitbucketCredentials(username, appkey)
