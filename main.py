#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python

import requests
from requests.auth import HTTPBasicAuth
import credentials
import argparse
from git import Repo
import os
from typing import List, Dict

import uidsread


def make_action():
    arguments = parse_cmd_arguments()
    bitbucket = arguments.gitserver and arguments.gitserver == "bitbucket"
    directory = arguments.directory
    if bitbucket:
        reviewers_list, bitbucket_credentials, pr_title, workspace = process_bitbucket_args(arguments)
    repo = Repo(directory)
    if arguments.newbranch:
        working_branch = arguments.newbranch
        repo.git.checkout('-b', arguments.newbranch)
    else:
        working_branch = repo.head
    execute_git_action(arguments, repo, working_branch)
    if bitbucket:
        json = create_pr_json(working_branch, reviewers_list)
        project = directory[directory.rfind('/') + 1:]
        create_pr_request(json, arguments.ws, project, bitbucket_credentials)


def create_pr_request(json: Dict, ws: str, project: str, credentials: credentials.BitbucketCredentials):
    API_ENDPOINT = f"https://api.bitbucket.org/2.0/repositories/{ws}/{project}/pullrequests"
    requests.post(url=API_ENDPOINT, json=json,
                  auth=HTTPBasicAuth(credentials.username, credentials.appkey))


def execute_git_action(arg: argparse.Namespace, repo: Repo, branch: str):
    repo.git.add(arg.add)
    repo.git.commit('-m', arg.commitmessage)
    repo.git.push('origin', branch)


def parse_cmd_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", nargs='+', default='--all')
    parser.add_argument("-m", "--commitmessage", type=str, required=True,
                        help="choose gitserver. Github or Bitbucket")
    parser.add_argument("-b", "--newbranch", type=str,
                        help="create new branch")
    parser.add_argument("-d", "--directory", type=str,
                        help="provide directory for gitproject. Default is current working directory",
                        default=os.getcwd())
    subparsers = parser.add_subparsers(dest='gitserver', help="choose gitserver. Github or Bitbucket")
    bitbucket_server = subparsers.add_parser('bitbucket')
    bitbucket_server.add_argument('-pr', type=str,
                                  help='Provide pull request title. Default is the same as a commit message')
    bitbucket_server.add_argument('-rv', type=str, nargs='+', required=True,
                                  help='Provide list of reviewers fo PR. '
                                       'You can put here json file or uids as a arguments')
    bitbucket_server.add_argument('-ws', type=str, required=True,
                                  help='Provide workspace for bitbucket repositories ')
    bitbucket_server.add_argument('-cd', type=str,
                                  help='Provide credentials file for bitbucket. For default program will look '
                                       'in your home directory')
    return parser.parse_args()


def process_arguments(args: argparse.Namespace):
    if args.gitserver and args.gitserver == "bitbucket":
        process_bitbucket_args(args)


def process_bitbucket_args(args: argparse.Namespace):
    if hasattr(args, 'rv'):
        reviewers_list = process_reviewers_arg(args.rv)
    else:
        reviewers_list = uidsread.get_users_for_given_workspace(args.ws)
    if args.cd:
        bitbucket_credentials = credentials.get_credentials_for_bitbucket(args.cd)
    else:
        bitbucket_credentials = credentials.get_credentials_for_bitbucket()
    pr_title = args.pr if args.pr else args.m
    # users = uidsread.get_users_for_given_workspace('piotrmucha1997')
    return reviewers_list, bitbucket_credentials, pr_title, args.ws


def process_reviewers_arg(rev: List[str]) -> List[Dict[str, str]]:
    reviewers: List[str] = rev
    if len(reviewers) == 1 and reviewers[0].endswith('.json'):
        reviewers_list = uidsread.get_json_array_from_file(reviewers[0])
    else:
        reviewers_list = uidsread.map_users_to_json_array(*reviewers)
    return reviewers_list


def create_pr_json(branch: str, reviewers: List[Dict[str, str]]):
    return {"title": "My Title",
            "source": {
                "branch": {
                    "name": branch
                }
            },
            "reviewers": reviewers
            }


# result = uidsread.get_json_array_from_file(args.reviewers)


if __name__ == '__main__':
    print(dirs[dirs.rfind('/') + 1:])
    # args = parse_cmd_arguments()
    # print(args)

# r = requests.post(url=API_ENDPOINT, json=data, auth=HTTPBasicAuth(userName, appkey))
