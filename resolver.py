#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python
"""Narzędzie do modyfikacji repozytoriow

Skrypt umozliwa zamiane wybranego ciagu znakow we wszystkich repozytoriach znajdujących
sie w obecnym katalogu na ciag znakow wybrany przez uzytkownika. Po zamianie ciagu znakow
skrypt commituje zmiany oraz wysyla na repozytorium. Istnieje rowniez szereg opcji takich jak
wystawienie pull requesta ze zmianami, dodanie do niego reviowerow, itp.

Skrypt nalezy wykonac w katalogu z repozytoriami gitowymi oraz argumentem -p
np. resolver.py -p repo-config.txt

Przykadowa zawartosc pliku configowego:

[PROPERTIES]
commit_message=test
str_to_find=useJUnitPlatform
str_to_repl=junit
master=master
checkout_to_master_before_work=yes
extensions=gradle java
[BITBUCKET]
branch=new_branch
workspace=piotrmucha1997

sekcja PROPERTIES => wymagana sekcja z ogolnymi ustawieniami
commit_message => wiadomosc commita, oraz tytul pull requesta (wymagane)
str_to_find => ciag znakow ktory zostanie zastopiony we wszystkich repozytoriach (wymagane)
str_to_repl => string do zastapienia (wymagane)
master => branch master w repozytoriach (wymagane)
checkout_to_master_before_work => skrypt zmienia branch na master we
                                 wszystkich repozytoriach (opcjonalne) przyjmuje wartosci yes/no
extenions => rozszerzenia zmienianych plików oddzielone spacją (wymagane)
stash_before_work => zrob stash przed zmianami (opcjonalne) przyjmuje wartosci yes/no
pull_before_work => zrob pull przed zmianami (opcjonalne) przyjmuje wartosci yes/no
sekcja BITBUCKET => opcjonalna sekcja z definicjami do wystawienia pull requesta
bitbucket-credentials => adres do pliku z credentialami do bitbucketa, domyslnie
skrypt szuka pliku w folderze home
Plik z credentailami musi mieć format:
[CREDENTIALS]
appkey=*******
userName=<nazwa_uzytkownika>
workspace => workspace z bitbucketa (wymagane)
reviewers => list revierow podana jako uidy oddzielone spacja, albo plik json. Domyslnie
            dodawani sa wszyscy rewierzy z workspace (opcjonalne)
branch => branch na ktorym nastepuja zmiany i wystawiany jest pull request (wyamgane)
prtitle => opcjonalny tytul pull requesta


"""
import argparse
import configparser
import glob
import os
import sys
from dataclasses import dataclass
from typing import List, Dict, Tuple

from git import Repo, NoSuchPathError, InvalidGitRepositoryError

import credentials
import gitaction
import uidsread
from gitaction import process_reviewers_arg


@dataclass
class ClassWithFlags:
    """
    Klasa przechowujaca logiczne atrybuty dla kongifuracji

    Atrybuty
    ----------
    stash_before_work : bool
        czy nalezy wykonac stas przed modyfikajcami
    checkout_to_master_before_work : bool
        czy nalezy zrobic checkout do mastera przed zmianami
    pull_before_work : bool
        czy nalezy zrobic pull przed zmianami
    """

    stash_before_work: bool
    checkout_to_master_before_work: bool
    pull_before_work: bool


def parse_bool_arguments(bool_dict: dict) -> ClassWithFlags:
    """
    Metoda parsujaca konfigurajce na klase z wartoscami logicznymi

    Parameters
    ----------
    bool_dict : bool
        slownik z konfigurajca dla lgoicznych elementow
    Returns
    -------
    ClassWithFlags
        klasa z wartoscami logicznymi
    """
    stash_before_work = parse_logical_arg("stash_before_work", bool_dict)
    checkout_to_master_before_work = parse_logical_arg("checkout_to_master_before_work", bool_dict)
    pull_before_work = parse_logical_arg("pull_before_work", bool_dict)
    return ClassWithFlags(stash_before_work, checkout_to_master_before_work,
                          pull_before_work)


def parse_logical_arg(key: str, options: dict):
    """
    Zwraca obiekt true jesli klucz istnieje i ma wartosc yes

    Parameters
    ----------
    key : bool
        klucz do sprawdzenia
    options : dict
        slownik z konnfiguracja
    Returns
    -------
        obiekt not null jesli istnieje i ma wartosc yes
    """
    return options.get(key) and options.get(key) == "yes"


def parse_args():
    """
    Parsuje plik z konfiguracja z cmd, waliduje czy zostal podany

    Returns
    -------
    sparsowany plik z konfiguracja
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--properties", type=str, required=True,
                        help='File with all properties')
    return parser.parse_args()


def get_properties_dict(properties_file: str) -> dict:
    """
    parsuje sekcje PROPERTIES z pliku z konfigurajca na slownik

    Parameters
    ----------
    properties_file : str
        adres pliku z konfiguracja
    Returns
    -------
    dict
        slownik z konfiguracja
    """
    config = configparser.RawConfigParser()
    config.read(properties_file)
    try:
        properties = dict(config.items('PROPERTIES'))
    except configparser.NoSectionError:
        print(f"Can't find {properties_file} file with section PROPERTIES.")
        sys.exit(1)
    return properties


def process_required_fields(properties: Dict[str, str]) -> Tuple:
    """
    Pobiera wymagane propertiesy ze slownika. Waliduje czy zostaly podane

    Parameters
    ----------
    properties : str
        slownik z konfigurajca
    Returns
    -------
    Tuple
        zwraca wiadomosc commita, string do znalezienia, string do zastapienia,
        rozszerzenia plikow, galaz mastera
    """
    commit_message = get_required_property("commit_message", properties)
    str_to_find = get_required_property("str_to_find", properties)
    str_to_repl = get_required_property("str_to_repl", properties)
    master = get_required_property("master", properties)
    extensions = get_required_property("extensions", properties).split()
    return commit_message, str_to_find, str_to_repl, extensions, master


def get_required_property(prop: str, properties: Dict[str, str]):
    """
    Pobiera wymagany properties ze slownika, zwraca blad jesli nie istenije

    Parameters
    ----------
    prop : str
        properties do sprawdzenia
    properties : str
        slownik z konfiguracja
    Returns
    -------
    Zwraca dany propertiess lub blad jesli nie istnieje
    """
    value = properties.get(prop)
    if value is None:
        print(f"You should provide required property: {prop}")
        sys.exit(1)
    return value


def has_bitbucket(file: str):
    """
    Sprawdza czy plik z konfigurajca ma sekcje BITBUCKET

    Parameters
    ----------
    file : str
        Plik z konfiguracja do sprawdzenia
    Returns
    -------
    Zwraca slownik ze slownikiem, z konfiguracja, lub False gdy jej nie ma
    """
    config = configparser.RawConfigParser()
    config.read(file)
    try:
        properties = dict(config.items('BITBUCKET'))
        return properties
    except configparser.NoSectionError:
        return False


def execute_script():
    """
        Metoda wykonuje logike skryptu. Jego opis znajduje się na samej gorze skrytpu.
    """
    arguments = parse_args()
    current_directory = os.getcwd()
    properties = get_properties_dict(arguments.properties)
    commit_message, str_to_find, str_to_repl, extensions, master = \
        process_required_fields(properties)
    bitbucket = has_bitbucket(arguments.properties)
    for project in next(os.walk(current_directory))[1]:
        abso = os.path.join(current_directory, project)
        try:
            repo = Repo(abso)
        except (InvalidGitRepositoryError, NoSuchPathError) as error:
            print(f"Cant create repository instance from {abso} ", error)
            continue
        execute_git_action(repo, parse_bool_arguments(properties), master,
                           get_required_property("branch", bitbucket) if bitbucket else None)
        matched_files = process_files(abso, extensions, str_to_find, str_to_repl)
        if len(matched_files) > 0:
            commit_add_push(repo, matched_files, commit_message)
            process_bitbucket(bitbucket, commit_message, project)
        else:
            print(f"Files with str not found in project {project}")


def process_files(abso: str, extensions: List[str], str_to_find: str, str_to_repl: str):
    """
    Wyszukuje pliki o podanych rozszerzeniach i zastepuje ciag znakow

    Parameters
    ----------
    abso : str
        sciezka do repozytorium
    extensions : List[str]
        lista rozszerzen plikow ktorych szukamy
    str_to_find : str
        lista rozszerzen plikow ktorych szukamy
    str_to_repl: str
        string ktorym zastepujemy stary
    Returns
    -------
    List[str]
        Zwraca liste zmienionych plikow
    """
    files = get_files_with_extension(abso, extensions)
    matched_files = find_files_with_str(files, str_to_find)
    modify_all_files(matched_files, str_to_find, str_to_repl)
    return matched_files


def process_bitbucket(bitbucket, commit_message: str, project: str):
    """
        Tworzy pull requesta w zaleznosci czy user skonfigurowal propertiesy dla bitbucketa.

        Parameters
        ----------
        bitbucket
            properitesy dla bitbucketa
        commit_message : str
            wiadomosc commita
        project : str
            projekt bitbucketowy
        """
    if bitbucket:
        reviewers_list, bitbucket_credentials, pr_title, workspace, branch \
            = process_bitbucket_properties(bitbucket, commit_message)
        json = gitaction.create_pr_json(branch, reviewers_list, pr_title)
        gitaction.create_pr_request(json, workspace, project, bitbucket_credentials)


def commit_add_push(repo: Repo, add: List[str], commit: str):
    """
    Wykonuje gitowe polecenia add, commit, i push dla obecnego brancza

    Parameters
    ----------
    repo : Repo
        obiekt repozytorium
    add : List[str]
        pliki do wykonania komendy add
    commit : str
        wiadomosc commita
    """
    repo.git.add(add)
    repo.git.commit('-m', commit)
    repo.git.push('origin', 'HEAD')


def modify_all_files(files: List[str], old_str: str, new_str: str):
    """
    Zastepuje wszystkie wystapeinia starego stringa nowym stringiem

    Parameters
    ----------
    files : List[str]
        lista plikow do zmiany
    old_str : str
        ciag znakow do zmiany
    new_str : str
        na co zmienic ciag znakow
    """
    for file in files:
        with open(file) as file1:
            new_content = file1.read().replace(old_str, new_str)

        with open(file, "w") as file2:
            file2.write(new_content)


def find_files_with_str(files: List[str], string_to_find: str) -> List[str]:
    """
    Znajduje i zwraca liste plikow z danym ciagiem znakow

    Parameters
    ----------
    files : List[str]
        lista plikow do przeszukania
    string_to_find : str
        ciag znakow do znalezienia
    Returns
    -------
    List[str]
        Zwraca liste plikow z danym ciageim znakow
    """
    files_with_str = []
    for file in files:
        with open(file) as open_file:
            if string_to_find in open_file.read():
                files_with_str.append(file)
    return files_with_str


def get_files_with_extension(abso: str, extensions: List[str]) -> List[str]:
    """
    Zwraca pliki z danym rozszerzeniem

    Parameters
    ----------
    abso : str
        adres gdzie szukamy plikow
    extensions : List[str]
        Lista rozszerzen
    Returns
    -------
    List[str]
        Lista plikow z podanymi rozszerzeniami
    """
    files = []
    for ext in extensions:
        files += glob.glob(f"{abso}/**/*.{ext}", recursive=True)
    return files


def execute_git_action(repo: Repo, arguments: ClassWithFlags, master: str, branch: str):
    """
    Wykonuje stash, checkout do mastera, pull, oraz tworzenie nowej galezi w zaleznosci
    od podanych wartosci logicznych

    Parameters
    ----------
    repo : Repo
        instancja repozytorium
    arguments : ClassWithFlags
        klasa z flagami
    master : str
        nazwa galezi master
    branch : str
        nazwa brancha do utworzenia i checkout
    """
    if arguments.stash_before_work:
        repo.git.stash('save')
    if arguments.checkout_to_master_before_work:
        repo.git.checkout(master)
    if arguments.pull_before_work:
        repo.git.pull()
    if branch:
        repo.git.checkout('-b', branch)


def process_bitbucket_properties(properties: dict, commit_message: str) -> Tuple:
    """
    Pobiera wymagana propertiesty Bitbukceta, jesli nie ma wymaganych pobiera domyslne.
    Dla listy revieroww pobiera wszystkich z projektu gdy nie dostarczymy.
    to zwraca blad

    Parameters
    ----------
    properties : dict
        slownik z propertiesami
    commit_message : str
        wiadomosc commita, jest zwracana gdy nie ma argumentu z nazwa pull requesta
    Returns
    -------
    Tuple
        Tuple z lista revierwerow, credentiale do bitbukceta, tytul pull requesta,
        workspace bitubkcketa, branch.
    """
    bitbucket_workspace = get_required_property("workspace", properties)
    if properties.get("bitbucket_credentials"):
        credential: str = properties.get("bitbucket_credentials")
        bitbucket_credentials = credentials.get_credentials_for_bitbucket\
            (credential)
    else:
        bitbucket_credentials = credentials.get_credentials_for_bitbucket()
    if properties.get("reviewers"):
        reviewers_list = process_reviewers_arg(properties.get("reviewers").split())
    else:
        reviewers_map = uidsread.get_users_for_given_workspace \
            (bitbucket_workspace, bitbucket_credentials)
        reviewers_list = uidsread.map_users_to_json_array(*reviewers_map)

    pr_title = properties.get("prtitle") if properties.get("prtitle") else commit_message
    branch = get_required_property("branch", properties)
    return reviewers_list, bitbucket_credentials, pr_title, bitbucket_workspace, branch


if __name__ == '__main__':
    execute_script()
