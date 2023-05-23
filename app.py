import json
from GithubGraphQL import  GithubGraphQL
from datetime import datetime
from functools import reduce

repo: str = None
token: str = None
last_update_time: datetime = None
ignore_list: list[int] = None
post_repo_url: str = None

with open("digest.setting.json", 'r+') as f:
    setting = json.load(f)

ql = GithubGraphQL(
    setting["token"],
    setting["owner"],
    setting["repo"],
    datetime.strptime(setting["last_update_time"], "%Y-%m-%dT%H:%M:%SZ"),
    setting["target_issue"]
    )
ql.createIssue()
r = ql.getResult()
datas = [r[k] for k in r]
events = [event for data in datas for event in data.toEvents()]
events.sort(key=lambda x: x.timestamp)
ql.sendData(events)

setting["last_update_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
setting["target_issue"] = ql.target_issue

with open("digest.setting.json", 'w') as f:
    json.dump(setting, f, indent=4)