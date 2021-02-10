#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python
import configparser
import requests
from requests.auth import HTTPBasicAuth
import json
from typing import Dict, List, Tuple
from credentials import get_credentials_for_bitbucket, BitbucketCredentials
import argparse
import os

API_USER = "https://api.bitbucket.org/2.0/user/"


def execute_script():
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str,
                        help="provide directory where to put downloaded credentials."
                             "For default program will put files in current working directory",
                        default=os.getcwd())
    parser.add_argument('-ws', type=str, required=True,
                        help='Provide a bitbucket workspace from which reviewers will be retrieved.')
    parser.add_argument('-cd', type=str,
                        help='Provide credentials file for bitbucket. For default program will look '
                             'for bitbucket-credentials file in your home directory')
    return parser.parse_args()


def get_users_for_given_workspace(workspace: str, credentials: BitbucketCredentials) -> Dict[str, str]:
    user_endpoint = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members"
    r = requests.get(user_endpoint, auth=HTTPBasicAuth(credentials.username, credentials.appkey))
    data = json.loads(r.content)
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
    p = requests.get(API_USER, auth=HTTPBasicAuth(credentials.username, credentials.appkey))
    data = json.loads(p.content)
    return data['uuid']


def map_users_to_json_array(*users_uids) -> List[Dict[str, str]]:
    result = []
    for uuid in users_uids:
        result.append({'uuid': uuid})
    return result


def create_two_json_with_reviewers(users_map: Dict[str, str], directory: str = os.getcwd()) -> None:
    with open(os.path.join(directory, 'usersMap.json'), 'w') as f:
        json.dump(users_map, f, ensure_ascii=False)
    with open(os.path.join(directory, 'reviewers.json'), 'w') as f:
        json.dump(map_users_to_json_array(*users_map), f, ensure_ascii=False)


def get_json_array_from_file(filename: str) -> List[Dict[str, str]]:
    with open(filename) as f:
        data = json.load(f)
    return data


if __name__ == '__main__':
    execute_script()
