from github import *
from api import rate_limit
import time

# developers = Developers.select().where(Developers.prev_downloaded == False).order_by(Developers.id).limit(5000)
# for d in developers:
#     remain, reset = rate_limit()
#     if remain < 100:
#         time.sleep(reset - time.time())
#     get_previous_projects(d)
#
# sql = 'SELECT full_name, age, size, commits, firm_involvement FROM repositories ORDER BY id LIMIT 150;'

repositories = Repositories.select().where(Repositories.internal_cohesion >> None).order_by(Repositories.id).limit(1001);
for r in repositories:
    update_repo(r)

# from github import *
# repo = Repositories.get(Repositories.full_name == "facebook/react")
# developers = Developers.select().join(Involvement).where(Involvement.repository == repo)
# involvements = []
# for d in developers:
#     involvements.append([i for i in Involvement.select().where(Involvement.developer == d)])
