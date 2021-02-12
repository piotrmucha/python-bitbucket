"""
Skrypt umozliwia pobranie credentiali dla bitbucketa
Skrypt umozliwa sparsowanie pliku z credentialami dla bitbukceta

Deifinuje jedna funkcje get_credentials_for_bitbucket ktora jest
uzywana przez inne skrypty

"""
from dataclasses import dataclass
import configparser
from pathlib import Path
import sys


@dataclass
class BitbucketCredentials:
    """
    Klasa przechowujaca username i appkey dla bitubkceta

    Atrybuty
    ----------
    username : str
        nazwa uzytkownika
    appkey : str
        appkey dla uzytkownika
    """
    username: str
    appkey: str


def get_credentials_for_bitbucket(credentials: str =
                                  f'{Path.home()}/bitbucket-credentials') -> BitbucketCredentials:
    """
    Metoda wyciagajaca credentiale do bitbukceta z pliku

    Parameters
    ----------
    credentials : str
        adres pliku z credentialami. Domyslnie szukany jest plik z home directory
    Returns
    -------
    BitbucketCredentials
        klasa z credentialami do bitbukceta
    """
    config = configparser.RawConfigParser()
    config.read(credentials)
    try:
        details_dict = dict(config.items('CREDENTIALS'))
    except configparser.NoSectionError:
        print(f"Can't find {credentials} file with section CREDENTIALS.")
        sys.exit(1)
    username = details_dict.get('username')
    appkey = details_dict.get('appkey')
    if username is None:
        print(f"Can't find username in {credentials} file ")
        sys.exit(1)

    if appkey is None:
        print(f"Can't find appkey in {credentials} file ")
        sys.exit(1)
    return BitbucketCredentials(username, appkey)
