from datetime import datetime
from string import Template

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

issue_template = """
# {title} [#{number}]({link})
created by {author} on {date}
{body}


"""

issue_modified_template = """
# {title} [#{number}]({link})
modified by {author} on {date}
{body}


"""

comment_template = """
{author} [commented]({link}) on {date}
{body}

"""

comment_modified_template = """
{author} modified [comment]({link}) on {date}
{body}

"""

convertToDateTime = lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")

format_date = lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
def trim_and_format(x: str) -> str:
    if len(x) > 200:
        x = x[:200] + "..."
    return ">" + x.strip().replace("\n", "\n> ")

class ModifiableItem:
    def __init__(self, graphqlResult: dict):
        self.editor = graphqlResult["editor"]["login"] if graphqlResult["editor"] else None
        self.edit_at = convertToDateTime(graphqlResult["lastEditedAt"]) if graphqlResult["lastEditedAt"] else None
        self.author = graphqlResult["author"]["login"]
        self.created_at = convertToDateTime(graphqlResult["createdAt"])
    
    @property
    def is_modified(self):
        return self.editor != None
    
    @property
    def last_change_date(self) -> datetime:
        return self.edit_at if self.is_modified else self.created_at
    
    @property 
    def last_change_author(self) -> str:
        return self.editor if self.is_modified else self.author
    
    def within_time_range(self, time_range: tuple[datetime, datetime]) -> bool:
        return self.last_change_date >= time_range[0] and self.last_change_date <= time_range[1]

class GitComment(ModifiableItem):
    def __init__(self, graphqlResult: dict):
        super().__init__(graphqlResult)
        self.source_link = graphqlResult["url"]
        self.body = graphqlResult["body"]

    def to_markdown(self):
        temp = comment_modified_template if self.is_modified else comment_template
        return temp.format(
                author=self.last_change_author,
                link=self.source_link,
                date=format_date(self.last_change_date),
                body=trim_and_format(self.body)
            )
    
    @property
    def is_deleted(self) -> bool:
        return self.body == None

class GitIssue(ModifiableItem):
    def __init__(self, graphqlResult: dict, timeRange: tuple[datetime, datetime]):
        super().__init__(graphqlResult)
        self.url = graphqlResult["url"]
        self.number = graphqlResult["number"]
        self.timeRange = timeRange
        self.title = graphqlResult["title"]
        self.id = graphqlResult["id"]
        self.body = graphqlResult["body"]
        self.comments = []
        
        self.read_paginated_data(graphqlResult)

    def read_paginated_data(self, graphqlResult:dict):
        self.last_comment_cursor = graphqlResult["comments"]["pageInfo"]["endCursor"] or "null"
        self.has_more_comments = graphqlResult["comments"]["pageInfo"]["hasNextPage"]

        for raw_comment in graphqlResult["comments"]["nodes"]:
            comment = GitComment(raw_comment)
            if comment.within_time_range(self.timeRange) and not comment.is_deleted:
                self.comments.append(comment)
    
    def draft_gql_query(self) -> str:
        return pr_issue_query.substitute(id=self.id, url=self.url, cursor=self.last_comment_cursor)

    @property
    def has_more_data(self) -> bool:
        return self.has_more_comments
    
    @property
    def total_changes(self) -> int:
        return len(self.comments)
    
    def to_markdown(self) -> str:
        temp = issue_modified_template if self.is_modified else issue_template
        header = temp.format(
            title=self.title,
            author=self.last_change_author,
            number=self.number,
            link=self.url,
            date=format_date(self.last_change_date),
            body=trim_and_format(self.body)
        )
        self.comments.sort(key=lambda x: x.last_change_date)
        return header + '\n'.join([comment.to_markdown() for comment in self.comments])
