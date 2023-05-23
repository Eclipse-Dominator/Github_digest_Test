from datetime import datetime
from string import Template
from git_classes.Event import Event

pr_issue_query = Template("""
$id: resource(url: "$url") {
    ... on Issue {
        comments(first:100, after: $cursor) {
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes{
                author {
                    login
                }
                url
                createdAt
                lastEditedAt
                body
                editor {
                    login
                }
            }
        }
    }
}
""")

convertToDateTime = lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")

class ModifiableItem:
    def __init__(self, graphqlResult: dict):
        self.editor = graphqlResult["editor"]["login"] if graphqlResult["editor"] else None
        self.edit_at = convertToDateTime(graphqlResult["lastEditedAt"]) if graphqlResult["lastEditedAt"] else None
        self.author = graphqlResult["author"]["login"]
        self.created_at = convertToDateTime(graphqlResult["createdAt"])

    def get_creator_mkdown(self):
        return f"created by @{self.author} on {self.created_at}\n"

    def get_editor_mkdown(self):
        return f"last edited by @{self.editor} on {self.edit_date}\n"
    
    @property
    def is_modified(self):
        return self.editor != None

class GitLabel:
    def __init__(self, graphqlResult: dict):
        self.name = graphqlResult["name"]
        self.created_at = convertToDateTime(graphqlResult["createdAt"])
        self.link = graphqlResult["url"]

    def toEvents(self):
        return [Event(self, self.created_at, f"{self.name} was added to {self.source_link}")]

class GitComment(ModifiableItem):
    def __init__(self, graphqlResult: dict):
        super().__init__(graphqlResult)
        self.source_link = graphqlResult["url"]
        self.body = graphqlResult["body"]


    def toMarkdown(self, txt:str):
        return f"""
[Comment]({self.source_link}) {txt}
<details>
<summary>View details</summary>

{self.body}

</details>
\n"""

    def toEvents(self) -> list[Event]:
        if self.body == None:
            return [] # Comment has been deleted, dont list it out
        if self.is_modified:
            return [Event(self, self.edit_at, self.toMarkdown(self.get_editor_mkdown()))]

        return [Event(self, self.created_at, self.toMarkdown(self.get_creator_mkdown()))]

class GitIssue(ModifiableItem):
    def __init__(self, graphqlResult: dict, timeRange: tuple[datetime, datetime]):
        super().__init__(graphqlResult)
        self.repoId = graphqlResult["url"].split("/")[-1]
        self.timeRange = timeRange
        self.title = graphqlResult["title"]
        self.id = graphqlResult["id"]
        self.comments = []
        
        self.readPaginatedData(graphqlResult)

    def readPaginatedData(self, graphqlResult:dict):
        self.last_comment_cursor = graphqlResult["comments"]["pageInfo"]["endCursor"] or "null"
        self.has_more_comments = graphqlResult["comments"]["pageInfo"]["hasNextPage"]

        for raw_comment in graphqlResult["comments"]["nodes"]:
            comment = GitComment(raw_comment)
            if comment.created_at >= self.timeRange[0] and comment.created_at <= self.timeRange[1]:
                self.comments.append(comment)
    
    def draftGraphQLQuery(self) -> str:
        return pr_issue_query.substitute(id=self.id, url=self.url, cursor=self.last_comment_cursor)

    @property
    def has_more_data(self) -> bool:
        return self.has_more_comments
    
    def toMarkdown(self) -> str:
        return f"{self.created_at}: {self.title} was 'created' by @{self.author}: {self.markdown_link}"
    
    def toEvents(self):
        ret: list[Event] = []
        ret.append(Event(self, self.created_at, self.toMarkdown()))
        for comment in self.comments:
            ret.extend(comment.toEvents())
        for label in self.labels:
            ret.extend(label.toEvents())
        return [e for e in ret if e.timestamp >= self.timeRange[0] and e.timestamp <= self.timeRange[1]]