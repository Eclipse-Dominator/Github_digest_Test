from ..tokens import TOKEN
from string import Template
url = "https://api.github.com/graphql"
header = {
        "Authorization": f"Bearer {TOKEN}",
    }


with open("graphql/send_comment.graphql", "r") as f:
    add_comment_query = Template(f.read())

with open("graphql/find_repo_id.graphql", 'r') as f:
    findRepoIdStr = Template(f.read())

class Query:
    def __init__(self):
        self.id = id

    def draft_query(self) -> str:
        return f"{id}: "
    
    def get_result(self, query) -> dict:
        return query[self.id]
    
    def send_query(self) -> 

class send_comment_query(Query):
    def __init__(self, id:str, subjectId: str, body: str):
        super().__init__(id)
        self.subjectId = subjectId
        self.body - body

    def draft_query(self) -> str:
        return f"{super().draft_query()}{add_comment_query.substitute(subjectId=self.subjectId, body=self.body)}"
    
class find_repo_id(Query):
    def __init__(self, id:str, subjectId: str, body: str):
        super().__init__(id)
        self.subjectId = subjectId
        self.body - body

    def draft_query(self) -> str:
        return f"{super().draft_query()}{add_comment_query.substitute(subjectId=self.subjectId, body=self.body)}"