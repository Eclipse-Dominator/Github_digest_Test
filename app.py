import json
from GithubGraphQL import  GithubGraphQL
from datetime import datetime


with open("digest.setting.json", 'r+') as f:
    setting = json.load(f)

ql = GithubGraphQL(
    setting["token"],
    setting["owner"],
    setting["repo"],
    setting["target_issue"],
    ignore_numbers=setting["ignore_list"]
    )

issues = ql.get_result()
ql.send_data(issues)

# setting["last_update_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
setting["target_issue"] = ql.target_issue
setting["ignore_list"] = ql.ignore_numbers

with open("digest.setting.json", 'w') as f:
    json.dump(setting, f, indent=4)