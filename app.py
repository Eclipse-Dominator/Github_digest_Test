import json
from digest_manager import  DigestManager
import os

if not os.path.exists("./digest.setting.json"):
    with open("digest.setting.json", 'w') as f:
        json.dump({
            "owner": os.environ["GITHUB_REPOSITORY_OWNER"],
            "repo": os.environ["GITHUB_REPOSITORY"],
            "target_issue": "",
            "ignore_list": []
        }, f, indent=4)

with open("digest.setting.json", 'r') as f:
    setting = json.load(f)

ql = DigestManager(
    setting["owner"],
    setting["repo"],
    setting["target_issue"],
    ignore_numbers=setting["ignore_list"]
    )

issues = ql.get_result()
ql.send_data(issues)

setting["target_issue"] = ql.target_issue
setting["ignore_list"] = ql.ignore_numbers

with open("digest.setting.json", 'w') as f:
    json.dump(setting, f, indent=4)