import api
from api import NoRepositoryFound
from itertools import combinations, product
import networkx as nx
from models import *


def get_repository(repo_name):
    try:
        repo = Repositories.get(Repositories.full_name == repo_name)
    except DoesNotExist:
        print("No repository data.\nFetch repo data from github.")
        # TODO fetch repo and save
        try:
            raw_repo = api.fetch_repo(repo_name)
        except NoRepositoryFound:
            return
        repo = Repositories.from_raw(raw_repo)
        q = Repositories.select().where(Repositories.github == raw_repo["id"])
        if q.count() == 1:
            repo = q.first()

        # Save all contributors data and calculate commit count
        raw_contributors = api.fetch_all_contributors(repo_name)
        Developers.create_from_raw(raw_contributors)
        commits = 0
        for c in raw_contributors:
            commits += c["contributions"]
        repo.commits = commits
        if len(raw_contributors) > 0:
            repo.manager_id = raw_contributors[0]["id"]
        repo.save()
        Involvement.create_from_raw(raw_contributors, repo.github)
    return repo


def get_previous_projects(developer):
    print("Start fetching previous projects of ", developer.login)
    if not developer.prev_downloaded:
        repos = api.fetch_repos_user_contributed_to(developer.login)
        print(repos)
        for r in repos:
            get_repository(r)
        developer.prev_downloaded = True
        developer.save()


def calc_cohesion(repo):
    count = 0
    developers = \
        Developers.select().join(Involvement)\
        .where(Involvement.repository == repo)
    developers = [d for d in developers]
    for x, y in combinations(developers, 2):
        print(x.login, y.login)
        projects_x = [i.repository for i in\
                      Involvement.select().where(Involvement.developer == x)]
        projects_y = [i.repository for i in\
                      Involvement.select().where(Involvement.developer == y)]
        for p in projects_x:
            if p in projects_y and p.github != repo.github:
                count += 1
    return count / (len(developers) * (len(developers) - 1))


def has_connection(cx, cy):
    link = 0
    projects_x = [i.repository for i in
                  Involvement.select().where(Involvement.developer == cx)]
    projects_y = [i.repository for i in
                  Involvement.select().where(Involvement.developer == cy)]
    for i, j in product(projects_x, projects_y):
        if i == j: link += 1
    return link


def link_of(contributors):
    links = []
    for cx, cy in combinations(contributors, 2):
        if has_connection(cx, cy) != 0:
            links.append((cx.login, cy.login))
    return links


def graph_of_contributors(contributors):
    labels = [c.login for c in contributors]
    links = link_of(contributors)
    G = nx.Graph()
    G.add_nodes_from(labels)
    G.add_edges_from(links)
    return G


def calc_degree(repo):
    developers = \
        Developers.select().join(Involvement)\
        .where(Involvement.repository == repo)
    developers = [d for d in developers]
    graph = graph_of_contributors(developers)
    return graph.degree()[repo.manager.login]


def update_repo(repo):
    if not repo.manager:
        manager = Developers.select().join(Involvement).where(Involvement.repository == repo).order_by(Involvement.commit_count).limit(1).first()
        repo.manager = manager
    repo.internal_cohesion = calc_cohesion(repo)
    repo.degree_centrality = calc_degree(repo)
    repo.save()
