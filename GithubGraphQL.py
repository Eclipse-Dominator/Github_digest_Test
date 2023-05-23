from datetime import datetime
from git_classes.GitStructures import GitIssue
from git_classes.Event import Event
from string import Template
import requests

with open("graphql/mainquery.query", "r") as f:
    query = Template(f.read())

with open("graphql/send_comment.graphql", "r") as f:
    addCommentStr = f.read()

with open("graphql/create_issue.graphql", "r") as f:
    createIssueStr = f.read()

class GithubGraphQL:
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": "",
    }

    cursor:str = None

    def __init__(self, token: str, owner:str, repo:str, timestamp: datetime, target_issue:str) -> None:
        self.headers["Authorization"] = f"token {token}"
        self.repo = repo
        self.timestamp = timestamp
        self.target_issue = target_issue
        self.complete = False

    def generate_query(self, additional_queries: list[str]) -> dict:
        compiled_query = "{{\n{}\n{}}}".format(
                query.substitute(repo = self.repo,
                    timestamp=self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    cursor=self.cursor or "null"),
                '\n'.join(additional_queries)
            )
        return {
            "query": compiled_query,
        }

    def run_query(self, additional_queries: list[str] = []) -> dict:
        request = requests.post(self.url, json=self.generate_query(additional_queries), headers=self.headers)
        print(request.json())
        return request.json()
    
    def getResult(self) -> list[GitIssue]:
        ret: dict[str, GitIssue] = {}
        extra = []
        while not self.complete or (extra := [ret[key].draftGraphQLQuery() for key in ret if ret[key].has_more_data]):
            res = self.run_query(extra)["data"]["main"]
            self.update_cursor(res["pageInfo"])
            self.convertData(res["nodes"], ret)
        return ret
    
    

    def update_cursor(self, graphqlResult: dict):
        self.cursor = f'"{graphqlResult["endCursor"]}"'
        self.complete = not graphqlResult["hasNextPage"]
    
    def convertData(self, graphqlResult: dict, ret: dict[str, GitIssue]):
        for raw_issue in graphqlResult:
            if (raw_issue):
                issue = GitIssue(raw_issue, (self.timestamp, datetime.now()))
                ret[issue.id] = issue
    
    def sendData(self, events: list[Event]):
        txt = Template("""
<details>
<summary><h2>Digest $time</h2></summary>

$details
</details>
""")
        payload = {
            'query': addCommentStr,
            'variables': {
                'subjectId': self.target_issue,
                'body': txt.substitute(details="\n\n---\n".join(event.to_markdown() for event in events), time=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
            }
        }
        res = requests.post(self.url, json=payload, headers=self.headers)
        print(res.json())

    def createIssue(self):
        if self.target_issue:
            return
        
        payload = {
            'query': createIssueStr,
            'variables': {
                'owner': owner,
                'repo': repo,
                'title': issue_title,
                'body': issue_body
            }
        }
        