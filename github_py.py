import requests, json, re, pickle
import pandas as pd
import networkx as nx
from datetime import datetime as dt
import matplotlib.pyplot as plt
import itertools

API_ROOT = 'https://api.github.com'
API_TOKEN = '6e7fe2b9d8c6da31a832de88eb69922e63c04f9b'
USER = 'Takamichi-tsutsumi'


class NoRepositoryError(Exception):
    pass


def str2dt(tstr):
    return dt.strptime(tstr, '%Y-%m-%dT%H:%M:%SZ')


def api_get(url):
    """
    @args: url
    $return: dict res, int status
    """
    global API_TOKEN, USER
    res = requests.get(url, auth=(USER, API_TOKEN))
    return res.json(), res.status_code


def rate_limit():
    global API_ROOT
    res, _ = api_get(API_ROOT + '/rate_limit')
    return res["resources"]["core"]["remaining"]


def get_repo(repo):
    """repo have to be shape of 'owner/name' """
    repo_pattern = re.compile('[a-zA-Z0-9-]+\/[a-zA-Z0-9-]+$')
    m = repo_pattern.match(repo)
    assert m.group() == repo
    global API_ROOT
    url = API_ROOT + '/repos/' + repo
    res, status  = api_get(url)
    if status == 404:
        raise NoRepositoryError("Repository not found: " + repo)
    return res


def basic_data_of(repo):
    repo_res = get_repo(repo)
    data = {}
    data["repository"] = repo_res["full_name"]
    data["owner_name"] = repo_res["owner"]["login"]
    data["owner_type"] = repo_res["owner"]["type"]
    data["is_fork"] = repo_res["fork"]
    data["size"] = repo_res["size"]
    data["language"] = repo_res["language"]
    data["forks"] = repo_res["forks"]
    data["watchers"] = repo_res["watchers"]
    data["created_at"] = repo_res["created_at"]
    data["pushed_at"] = repo_res["pushed_at"]
    data["age (days)"] = (str2dt(data["pushed_at"]) - str2dt(data["created_at"])).days
    return data


def get_contributors_of(repo, per_page=30, page=1):
    url = API_ROOT + '/repos/' + repo + '/contributors?page=' + str(page) + '&per_page=' + str(per_page)
    print("Start fetching contributors of "+repo)
    res, status = api_get(url)
    if status == 200:
        return res
    else:
        raise NoRepositoryError


def repo_url_to_repo(url):
    tokens = url.split("/")
#     print(tokens)
    l = len(tokens)
    return tokens[l-2] + "/" + tokens[l-1]


def is_contributor_of(repo, user):
    n = 100
    i = 1
    all_contributors = []
    while n == 100:
        contributors = get_contributors_of(repo, per_page=100, page=i)
        if user in [c["login"] for c in contributors]:
            return True
        n = len(contributors)
        i += 1
    return False


def repos_user_contributed_to(user):
    issues_url = API_ROOT + '/search/issues?q=type:pr+author:' + user + '&per_page=100/page=1'
    res, status = api_get(issues_url)
    if status != 200:
        return []
    else:
        repos = list(set([repo_url_to_repo(pr['repository_url']) for pr in res["items"]]))
        return [r for r in repos if is_contributor_of(r, user)]


def contributors(repo):
    data = []
    contributors = get_contributors_of(repo, per_page=100)
    for c in contributors:
        user = {
            "id": c["id"],
            "name": c["login"],
            "contributions": c["contributions"]
        }
        repos = repos_user_contributed_to(c["login"])
        user["previous_projects"] = repos
        data.append(user)
    return data


def formatted_data(repo):
    data = {}
    print("Start fetching repository data...")
    data["basic"] = basic_data_of(repo)
    print("Successfully fetched repository data!")
    print("Start fetching contributors data...")
    c = contributors(repo)
    print("Successfully fetched contributors data!")
    data["contributors"] = c
    return data


def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename)


def save_contributors_of(repo_data):
    df = pd.DataFrame(repo_data["contributors"])
    df.to_csv(repo_data["basic"]["repository"].replace('/', '_') + '.csv')

if __name__ == '__main__':
    data = formatted_data('Takamichi-tsutsumi/onocolo-client')
    print(data)
    save_to_csv(data, 'onocolo.csv')
