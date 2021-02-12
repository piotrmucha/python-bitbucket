#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python
"""Skrypt do wykonywania operacji gitowych na pojedycznym repozytoirum

Skrypt umozliwa wykonywanie akcji na repozytoirum gitowym
Przjmuje argumenty konsolowe za pomoca ktorych skrypt automatycznie
swykona commit, push, pull oraz wystawi pull requesta (w zależnosci od konfiguracji)
Pelna lista dostepnych opcji znajduje sie w funkcji parse_cmd_arguments i mozna
uzyskac dokumentacji opcji wykonujac" gitaction.py -h


Skrypt definuje rowniez szereg funkcji z ktorych korzysta skrypt resolver.py
Te funkcje to:

"""
import argparse
import os
from typing import List, Dict, Tuple

import requests
from git import Repo
from requests.auth import HTTPBasicAuth

import credentials
import uidsread


def make_action():
    """
    Metoda wykonuje logike skryptu, gdy uruchomimy ten skrypt osobno. Opis parametrow znajduje sie
    w metodzie parse_cmd_arguments
    """
    arguments = parse_cmd_arguments()
    bitbucket = arguments.gitserver and arguments.gitserver == "bitbucket"
    directory = arguments.directory
    if bitbucket:
        reviewers_list, bitbucket_credentials, pr_title, workspace = \
            process_bitbucket_args(arguments)
    repo = Repo(directory)
    if arguments.newbranch:
        working_branch = arguments.newbranch
        repo.git.checkout('-b', arguments.newbranch)
    else:
        working_branch = repo.head
    execute_git_action(arguments, repo, working_branch)
    if bitbucket:
        if arguments.newbranch is None:
            print("You should add newbranch argument when you would like to create PR")

        json = create_pr_json(working_branch, reviewers_list, pr_title)
        project = directory[directory.rfind('/') + 1:]
        create_pr_request(json, workspace, project, bitbucket_credentials)


def create_pr_request(json: Dict, workspace: str, project: str,
                      cred: credentials.BitbucketCredentials):
    """
    Metoda tworzaca pull requesta na bitbuckecie

    Parameters
    ----------
    json : Dict
        slownik z konfigurajca dla pull requesta
    workspace : str
        working space dla bitbucketa
    project : str
        projekt na bitbukcecie
    cred : BitbucketCredentials
        credentiale dla bitbucketa
    Returns
    -------
    ClassWithFlags
        klasa z wartoscami logicznymi
    """
    api_endpoint = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{project}/pullrequests"
    request = requests.post(url=api_endpoint, json=json,
                            auth=HTTPBasicAuth(cred.username, cred.appkey))
    if request.status_code == 201:
        print("pull request created successfully")
    else:
        print("cant create pr!", request.content)


def execute_git_action(arg: argparse.Namespace, repo: Repo, branch: str):
    """
    Metoda wykonuje gitowy add, commit i push bazujac na argumentach

    Parameters
    ----------
    arg : Namespace
        argumenty konsolowe
    arg : Repo
        instancja repozytorium
    branch : str
        branch ktory pushujmey

    """
    repo.git.add(arg.add)
    repo.git.commit('-m', arg.commitmessage)
    repo.git.push('origin', branch)


def parse_cmd_arguments() -> argparse.Namespace:
    """
    Metoda parsuje argumetny z commendlina i zwraca sparsowane Namespace

    Returns
    -------
    Namespace
        sparsowany obiekt Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", nargs='+', default='--all')
    parser.add_argument("-m", "--commitmessage", type=str, required=True,
                        help="choose gitserver. Github or Bitbucket")
    parser.add_argument("-b", "--newbranch", type=str,
                        help="create new branch")
    parser.add_argument("-d", "--directory", type=str,
                        help="provide directory for gitproject. "
                             "Default is current working directory",
                        default=os.getcwd())
    subparsers = parser.add_subparsers(dest='gitserver',
                                       help="choose gitserver. Github or Bitbucket")
    bitbucket_server = subparsers.add_parser('bitbucket')
    bitbucket_server.add_argument('-pr', type=str,
                                  help='Provide pull request title. '
                                       'Default is the same as a commit message')
    bitbucket_server.add_argument('-rv', type=str, nargs='+', required=True,
                                  help='Provide list of reviewers fo PR. '
                                       'You can put here json file or uids as a arguments')
    bitbucket_server.add_argument('-ws', type=str, required=True,
                                  help='Provide workspace for bitbucket repositories ')
    bitbucket_server.add_argument('-cd', type=str,
                                  help='Provide credentials file for bitbucket. '
                                       'For default program will look '
                                       'in your home directory')
    return parser.parse_args()


def process_bitbucket_args(args: argparse.Namespace) -> Tuple:
    """
    Metoda parsuje argumenty zwiazene z bitbucketem.
    Gdy argumenty nie sa podane, pobierane sa domyslne wartosci

    Parameters
    ----------
    args : Namespace
        argumenty do sparsowania

    Returns
    -------
    Tuple
        zwracana jest lista reviewrow, credentiale dla bitbucketa, tytul pull requesta,
        workspace dla bitbucketa
    """
    if args.cd:
        bitbucket_credentials = credentials.get_credentials_for_bitbucket(args.cd)
    else:
        bitbucket_credentials = credentials.get_credentials_for_bitbucket()
    if hasattr(args, 'rv'):
        reviewers_list = process_reviewers_arg(args.rv)
    else:
        reviewers_map = uidsread.get_users_for_given_workspace(args.ws, bitbucket_credentials)
        reviewers_list = uidsread.map_users_to_json_array(*reviewers_map)

    pr_title = args.pr if args.pr else args.commitmessage
    return reviewers_list, bitbucket_credentials, pr_title, args.ws


def process_reviewers_arg(rev: List[str]) -> List[Dict[str, str]]:
    """
    Metoda konwertuje liste uidow uzytkownikow na slownik ktory
    jest potem konwertowany na jsona

    Parameters
    ----------
    rev : List[str]
        lista reviewrow
    Returns
    -------
    List[Dict[str, str]]
        Lista revierow w formacie ktory oczekuje api bitbucketa
    """
    reviewers: List[str] = rev
    if len(reviewers) == 1 and reviewers[0].endswith('.json'):
        reviewers_list = uidsread.get_json_array_from_file(reviewers[0])
    else:
        reviewers_list = uidsread.map_users_to_json_array(*reviewers)
    return reviewers_list


def create_pr_json(branch: str, reviewers: List[Dict[str, str]], pr_title: str) -> Dict:
    """
    Metoda tworzy jsona w formacie ktory jest oczekiwany prez api bitubketa

    Parameters
    ----------
    branch : str
        branch od ktorego jest tworzony pull request
    reviewers : List[Dict[str, str]]
        lista reviewrow
    pr_title : str
        tytul pull requesta
    Returns
    -------
    Dict
        json dla tworzenia pull requesta
    """
    return {"title": pr_title,
            "source": {
                "branch": {
                    "name": branch
                }
            },
            "reviewers": reviewers
            }


if __name__ == '__main__':
    make_action()
