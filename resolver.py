#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python

import argparse
import os
from pathlib import Path
import configparser
import uidsread
import credentials
from main import process_reviewers_arg
from typing import List
from dataclasses import dataclass
from git import Repo, NoSuchPathError, InvalidGitRepositoryError
import glob


@dataclass
class ClassWithFlags:
    use_regex: bool = False
    stash_before_work: bool = True
    checkout_to_master_before_work: bool = True
    pull_before_work: bool = True
    not_create_pr: bool = False


def parse_bool_arguments(c: dict) -> ClassWithFlags:
    use_regex = parse_logical_arg("use_regex", c)
    stash_before_work = parse_logical_arg("stash_before_work", c)
    checkout_to_master_before_work = parse_logical_arg("checkout_to_master_before_work", c)
    pull_before_work = parse_logical_arg("pull_before_work", c)
    not_create_pr = parse_logical_arg("not_create_pr", c)
    return ClassWithFlags(use_regex, stash_before_work, checkout_to_master_before_work,
                          pull_before_work, not_create_pr)


def parse_logical_arg(key: str, options: dict) -> bool:
    return options.get(key) and options.get(key) == "yes"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--properties", type=str, required=True,
                        help='File with all properties')
    return parser.parse_args()


def parse_properties_file(file: str = f'{Path.home()}/repositories.properties') -> dict:
    config = configparser.RawConfigParser()
    config.read(file)
    try:
        properties = dict(config.items('PROPERTIES'))
    except configparser.NoSectionError:
        print(f"Can't find {file} file with section PROPERTIES.")
        exit(1)
    return properties


def execute_script():
    arguments = parse_args()
    options = parse_properties_file(arguments.properties)
    current_directory = os.getcwd()
    _, dirs, _ = next(os.walk(current_directory))
    directories = dirs
    string_to_find = options.get('string_to_replace')
    reviewers_list, bitbucket_credentials, pr_title, workspace = process_bitbucket_properties(options)
    bool_arguments: ClassWithFlags = parse_bool_arguments(options)
    for project in directories:
        abso = os.path.join(current_directory, project)
        try:
            repo = Repo(abso)
        except (InvalidGitRepositoryError, NoSuchPathError) as error:
            print(f"Cant create repository instance from {abso} ", error)
            continue
        execute_git_action(repo, bool_arguments)
        extensions = ['hej']
        files = get_files_with_extension(abso, extensions)
        result = modify_files(files, string_to_find, bool_arguments.use_regex)


def modify_files(files: List[str], string_to_find: str) -> List[str]:
    files_with_str = []
    for file in files:
        with open(file) as open_file:
            if string_to_find in open_file.read():
                files_with_str.append(file)


def get_files_with_extension(abso, *extension):
    files = []
    for ext in extension:
        files += glob.glob(f"{abso}/**/*.{ext}", recursive=True)
    return files


def execute_git_action(repo: Repo, arguments: ClassWithFlags):
    if arguments.checkout_to_master_before_work:
        repo.git.checkout('master')
    if arguments.pull_before_work:
        repo.git.pull()
    if arguments.stash_before_work:
        repo.git.stash('save')


def process_bitbucket_properties(properties: dict):
    if properties.get("workspace"):
        bitbucket_workspace = properties.get("workspace")
    else:
        print("Error!. Can't find workspace section in properties file!")
        exit(1)

    if properties.get("reviewers"):
        reviewers_list = process_reviewers_arg(bitbucket_workspace)
    else:
        reviewers_list = uidsread.get_users_for_given_workspace(bitbucket_workspace)
    if properties.get("bitbucket_credentials"):
        bitbucket_credentials = credentials.get_credentials_for_bitbucket(properties.get("bitbucket_credentials"))
    else:
        bitbucket_credentials = credentials.get_credentials_for_bitbucket()
    pr_title = properties.get("prtitle") if properties.get("prtitle") else properties.get("commit_message")
    bitbucket_workspace = properties.get("workspace")
    return reviewers_list, bitbucket_credentials, pr_title, bitbucket_workspace


if __name__ == '__main__':
    execute_script()
