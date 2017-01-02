import os
import requests, json, re
from datetime import datetime as dt
from models import *

API_ROOT = 'https://api.github.com'
API_TOKEN = os.environ.get('github_api_token')
USER = 'Takamichi-tsutsumi'


class NoRepositoryFound(Exception):
    pass


def repo_url_to_repo(url):
    tokens = url.split("/")
    l = len(tokens)
    return tokens[l-2] + "/" + tokens[l-1]


def api_get(url):
    """
    @args: url
    $return: dict res, int status
    """
    global API_TOKEN, USER
    res = requests.get(url, auth=(USER, API_TOKEN))
    if res.status_code == 200:
        return res.json(), res.status_code
    else:
        return [], res.status_code



def rate_limit():
    global API_ROOT
    res, _ = api_get(API_ROOT + '/rate_limit')
    return res["resources"]["core"]["remaining"], res["resources"]["core"]["reset"]


def fetch_repo(repo_name):
    """repo have to be shape of 'owner/name' """
    print("Fetching repository")
    global API_ROOT
    url = API_ROOT + '/repos/' + repo_name
    res, status = api_get(url)
    if status != 200:
        raise NoRepositoryFound("Repository not found: " + repo_name)
    return res


def fetch_all_contributors(repo_name):
    page = 1
    count = 100
    contributors = []
    while count == 100:
        print("Fetchin all contributors of ", repo_name, " page ", page)
        url = API_ROOT + '/repos/' + repo_name + '/contributors?page=' + str(page) + '&per_page=100'
        res, status = api_get(url)
        print(len(res))
        if status == 200:
            contributors.extend(res)
            count = len(res)
            page += 1
        else:
            return contributors
    return contributors


def is_contributor_of(repo, user):
    r = Repositories.get(Repositories.full_name == repo)
    d = Developers.get(Developers.login == user)
    try:
        Involvement.get(Involvement.developer == d, Involvement.repository == r)
        return True
    except DoesNotExist:
        return False


def fetch_repos_user_contributed_to(user):
    page = 1
    count = 100
    all_repos = []
    while count == 100:
        print("Fetching repos user contributed to, page ", page)
        issues_url = API_ROOT + '/search/issues?q=type:pr+author:' + user + '&per_page=100&page=' + str(page)
        res, status = api_get(issues_url)

        if status != 200:
            return []
        else:
            repos = set([repo_url_to_repo(pr['repository_url']) for pr in res["items"]])
            all_repos.extend(list(repos))
        count = len(res)
        page += 1
    return all_repos


def search_repos():
    p = 1
    status = 200
    repos = []
    while 20 >= p and status == 200:
        url = API_ROOT + '/search/repositories?q=language:javascript+created:>2014-01-01&sort=stars&order=desc&per_page=100&page=' + str(p)
        res, status = api_get(url)
        if status == 200:
            repos.extend([r["full_name"] for r in res["items"]])
        p += 1
    return repos
