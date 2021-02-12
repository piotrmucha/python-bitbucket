#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python
"""Skrypt umozliwa wyciaganie informacji o oidach uzytkownikow danego workspace
    bitbucketa.

Definiuje tez funkcje zwiazane z oidami i ich konwersja z czego korzystaja inne skrypty

"""
import argparse
import json
import os
from typing import Dict, List

import requests
from requests.auth import HTTPBasicAuth

from credentials import get_credentials_for_bitbucket, BitbucketCredentials

API_USER = "https://api.bitbucket.org/2.0/user/"


def execute_script():
    """
    Metoda wykonuje logike skryptu, gdy uruchomimy ten skrypt osobno. Opis parametrow znajduje sie
    w pliku parse_cmd_arguments
    """
    arguments = parse_cmd_arguments()
    if arguments.cd:
        bitbucket_credentials = get_credentials_for_bitbucket(arguments.cd)
    else:
        bitbucket_credentials = get_credentials_for_bitbucket()
    users_map = get_users_for_given_workspace(arguments.ws, bitbucket_credentials)
    directory = arguments.directory
    if directory:
        create_two_json_with_reviewers(users_map, directory)
    else:
        create_two_json_with_reviewers(users_map)


def parse_cmd_arguments() -> argparse.Namespace:
    """
    Metoda parsuje argumetny z commendlina i zwraca sparsowane Namespace

    Returns
    -------
    Namespace
        sparsowany obiekt Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str,
                        help="provide directory where to put downloaded credentials."
                             "For default program will put files in current working directory",
                        default=os.getcwd())
    parser.add_argument('-ws', type=str, required=True,
                        help='Provide a bitbucket workspace from '
                             'which reviewers will be retrieved.')
    parser.add_argument('-cd', type=str,
                        help='Provide credentials file for bitbucket. '
                             'For default program will look '
                             'for bitbucket-credentials file in your home directory')
    return parser.parse_args()


def get_users_for_given_workspace(workspace: str,
                                  credentials: BitbucketCredentials) -> Dict[str, str]:
    """
    Funkcja zwraca slownik uuidow dla uzytkownikow, dla obecnego workspace.
    Usuwa przy tym obecnego uzytkownika, wykonujac zapytanie o jego uuida.

    Parameters
    ----------
    workspace: str
        workspace do przeszukania
    credentials: BitbucketCredentials
        credentiale do bitbukceta
    Returns
    -------
    Dict[str, str]
       slownik uzytkownik => uuid
    """
    user_endpoint = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members"
    request = requests.get(user_endpoint,
                           auth=HTTPBasicAuth(credentials.username, credentials.appkey))
    data = json.loads(request.content)
    data = data['values']
    users_map = dict()
    for i in data:
        user = i['user']
        users_map[user['uuid']] = user['display_name']
    current_user_uuid = get_uuid_for_current_user(credentials)
    if current_user_uuid in users_map:
        del users_map[current_user_uuid]
    return users_map


def get_uuid_for_current_user(credentials: BitbucketCredentials) -> str:
    """
    Funkcja wykonuje requesta ktory zwraca uuida dla obecnego uzytkownika
    bazujac na credentaialch

    Parameters
    ----------
    credentials: BitbucketCredentials
        credentiale do bitbukceta
    Returns
    -------
    str
       uuid dla obecnego uzytkownika
    """
    request = requests.get(API_USER, auth=HTTPBasicAuth(credentials.username, credentials.appkey))
    data = json.loads(request.content)
    return data['uuid']


def map_users_to_json_array(*users_uids) -> List[Dict[str, str]]:
    """
    Metoda zamienia liste oidow na format oczekiwany przez api bitbucketa

    Parameters
    ----------
    users_uids
        lista oidow w formacie nargs
    Returns
    -------
    List[Dict[str, str]]
       sparsowana tablica oidow
    """
    result = []
    for uuid in users_uids:
        result.append({'uuid': uuid})
    return result


def create_two_json_with_reviewers(users_map: Dict[str, str], directory: str = os.getcwd()) -> None:
    """
    Metoda tworzy dwa pliki json z reviewerami. Jeden plik jest w formacie
    ktory oczekuje api bitbucketa a drugi jest informacyjny dla uzytkownika.
    Ktory username przypada do jakiego uida

    Parameters
    ----------
    users_map : Dict[str, str]
        mapa uzytkownikow username => oid
    directory : str
        folder w ktorym beda zapisane pliki. Domyslnie katalog obecny.
    """
    with open(os.path.join(directory, 'usersMap.json'), 'w') as file1:
        json.dump(users_map, file1, ensure_ascii=False)
    with open(os.path.join(directory, 'reviewers.json'), 'w') as file2:
        json.dump(map_users_to_json_array(*users_map), file2, ensure_ascii=False)


def get_json_array_from_file(filename: str) -> List[Dict[str, str]]:
    """
    Metoda wczytuje plik json i zwraca jego zawartosc w formie Listy ze slownikiem

    Parameters
    ----------
    filename : str
        adres pliku
    Returns
    -------
    List[Dict[str, str]]
       sparsowana zawartosc pliku json
    """
    with open(filename) as file:
        data = json.load(file)
    return data


if __name__ == '__main__':
    execute_script()
