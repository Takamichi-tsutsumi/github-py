from github import *
from api import rate_limit
import time

developers = Developers.select().where(Developers.prev_downloaded == False).order_by(Developers.id).limit(1000)
for d in developers:
    remain, reset = rate_limit()
    if remain < 100:
        time.sleep(reset - time.time())
    get_previous_projects(d)
