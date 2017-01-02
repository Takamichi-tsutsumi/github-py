import api
from api import NoRepositoryFound
from itertools import combinations, product
import time
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


#########################################################
# Calculate network characteristics
#########################################################

def calc_cohesion(repo, involvements):
    count = 0
    for projects_x, projects_y in combinations(involvements, 2):
        for p in projects_x:
            for q in projects_y:
                if p.repository_id == q.repository_id and p.repository_id != repo.github:
                    count += 1
    if len(involvements) == 1:
        molecule = 1
    else:
        molecule = (len(involvements) * (len(involvements) - 1))
    return count / molecule


def has_link(projects_x, projects_y, repo):
    for x in projects_x:
        for y in projects_y:
            if x.repository_id == y.repository_id and x.repository_id != repo.github:
                return True
    return False


def links_of(involvements, repo):
    links = []
    for projects_x, projects_y in combinations(involvements, 2):
        link = 0
        if has_link(projects_x, projects_y, repo):
            links.append((projects_x[0].developer_id, projects_y[0].developer_id))
    return links


def calc_degree(repo, developers, involvements):
    labels = [c.github for c in developers]
    links = links_of(involvements, repo)
    graph = nx.Graph()
    graph.add_nodes_from(labels)
    graph.add_edges_from(links)
    return graph.degree()[repo.manager.github]


def update_repo(repo):
    print("Start updating repository:", repo.full_name)
    t = time.time()
    if not repo.manager:
        print("Querying Manager")
        manager = Developers.select().join(Involvement).where(Involvement.repository == repo).order_by(Involvement.commit_count).limit(1).first()
        repo.manager = manager
        print("Manager is ", manager.login)
    developers = [d for d in Developers.select().join(Involvement)
                  .where(Involvement.repository == repo)]
    involvements = []  # nested array
    print("Querying Involvement")
    for d in developers:
        involvements.append([i for i in Involvement.select().where(Involvement.developer == d)])
    print("Calculationg cohesion")
    repo.internal_cohesion = calc_cohesion(repo, involvements)
    print("Calculationg degree centrality")
    repo.degree_centrality = calc_degree(repo, developers, involvements)
    repo.save()
    print("Finish Updating repo. \n  It took", time.time() - t, "sec")
