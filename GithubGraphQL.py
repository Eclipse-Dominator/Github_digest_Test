from datetime import datetime, timedelta
from git_classes.GitStructures import GitIssue
from git_classes.Event import Event
from string import Template
import requests

with open("graphql/mainquery.query", "r") as f:
    query = Template(f.read())

with open("graphql/send_comment.graphql", "r") as f:
    add_comment_str = f.read()

with open("graphql/create_issue.graphql", "r") as f:
    create_issue_str = f.read()

with open("graphql/find_repo_id.graphql", 'r') as f:
    find_repo_id_str = Template(f.read())

with open("graphql/read_issue.graphql", 'r') as f:
    read_issue_str = Template(f.read())

digest_header = """<details>
<summary>
<h2>Digest Summary: {time}</h2>
<p>Tracked {all_changes} changes across {issues_changed} issues</p>
<p>Last updated: {time}</p>
</summary>

{body}

</summary>
"""

digest_content = """
Subscribe to this issue to receive a digest of all the issues in this repository.
Total digests -> {total_digests}
Last updated -> {last_update_time}
"""

class GithubGraphQL:

    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": "",
    }
    cursor:str = None
    owner: str
    repo: str
    timestamp: datetime
    target_issue: str
    complete: bool
    ignore_numbers: list[int]
    last_update_time: datetime
    total_digests: int

    def __init__(self, token: str, owner:str, repo:str, target_issue:str, ignore_numbers=[]) -> None:
        self.headers["Authorization"] = f"token {token}"
        self.owner = owner
        self.repo = repo
        self.target_issue = target_issue
        self.complete = False
        self.ignore_numbers = ignore_numbers
        self.total_digests = 0
        self.last_update_time = datetime.now() - timedelta(days=1)
        self.create_issue()
        self.retrieve_last_changes()


    @property
    def repo_repr(self):
        return f"{self.owner}/{self.repo}"

    def generate_query(self, additional_queries: list[str]) -> dict:
        compiled_query = "{{\n{}\n{}}}".format(
                query.substitute(repo = self.repo_repr,
                    timestamp=self.last_update_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    cursor=self.cursor or "null"),
                '\n'.join(additional_queries)
            )
        return {
            "query": compiled_query,
        }

    def run_query(self, additional_queries: list[str] = []) -> dict:
        request = requests.post(self.url, json=self.generate_query(additional_queries), headers=self.headers)
        return request.json()
    
    def get_result(self) -> list[GitIssue]:
        ret: dict[str, GitIssue] = {}
        extra = []
        while not self.complete or (extra := [ret[key].draft_gql_query() for key in ret if ret[key].has_more_data]):
            res = self.run_query(extra)["data"]["main"]
            self.update_cursor(res["pageInfo"])
            self.convert_data(res["nodes"], ret)
        
        return [ret[key] for key in ret]
    
    def update_cursor(self, graphqlResult: dict):
        self.cursor = f'"{graphqlResult["endCursor"]}"'
        self.complete = not graphqlResult["hasNextPage"]
    
    def convert_data(self, graphqlResult: dict, ret: dict[str, GitIssue]):
        for raw_issue in graphqlResult:
            if (raw_issue and raw_issue["number"] not in self.ignore_numbers):
                issue = GitIssue(raw_issue, (self.last_update_time, datetime.now()))
                ret[issue.id] = issue
    
    def send_data(self, issues: list[GitIssue]):
        payload = {
            'query': add_comment_str,
            'variables': {
                'subjectId': self.target_issue,
                'body': digest_header.format(
                    time=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    all_changes=sum([issue.total_changes for issue in issues]),
                    issues_changed=len(issues),
                    body='\n'.join([issue.to_markdown() for issue in issues])
                ),
                'update_body': self.get_update_body(datetime.now())
            }
        }
        res = requests.post(self.url, json=payload, headers=self.headers)
        print(res.json())

    def find_repo_id(self) -> str:
        payload = {
            'query': find_repo_id_str.substitute(owner=self.owner, repo=self.repo)
        }
        res = requests.post(self.url, json=payload, headers=self.headers)
        return res.json()["data"]["repository"]["id"]
    
    def retrieve_last_changes(self):
        payload = {
            'query': read_issue_str.substitute(issue_id=self.target_issue)
        }
        res = requests.post(self.url, json=payload, headers=self.headers).json()
        print(res)
        self.parse_issue_body(res["data"]["node"]["body"])
    
    def parse_issue_body(self, body: str):
        keywords = ["Total digests", "Last updated"]
        for line in body.split('\n'):
            if line.strip().startswith(keywords[0]):
                self.total_digests = int(line.split('->')[1].strip())
            elif line.strip().startswith(keywords[1]):
                self.last_update_time = datetime.strptime(line.split('->')[1].strip(), "%Y-%m-%dT%H:%M:%SZ")


    def get_update_body(self, time)-> str:
        return digest_content.format(
                total_digests=self.total_digests + 1,
                last_update_time=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )


    def create_issue(self):
        if self.target_issue:
            # issue already exist
            return 
        repo_id = self.find_repo_id()
        payload = {
            'query': create_issue_str,
            'variables': {
                'repoId': repo_id,
                'title': "Issues Digest",
                'body': digest_content.format(
                    total_digests=self.total_digests,
                    last_update_time=self.last_update_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                )
            }
        }
        issue_result = requests.post(self.url, json=payload, headers=self.headers).json()["data"]["createIssue"]["issue"]
        self.target_issue = issue_result["id"]
        self.ignore_numbers.append(issue_result["number"])

