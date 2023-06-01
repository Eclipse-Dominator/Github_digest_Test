import json
from digest_manager import  DigestManager
import os

def create_digest_setting():
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    with open("digest.setting.json", 'w') as f:
        json.dump({
            "owner": owner,
            "repo": repo,
            "target_issue": "",
            "ignore_list": []
        }, f, indent=4)

if not os.path.exists("./digest.setting.json"):
    create_digest_setting()

with open("digest.setting.json", 'r') as f:
    try:
        setting = json.load(f)
    except json.decoder.JSONDecodeError:
        create_digest_setting()
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