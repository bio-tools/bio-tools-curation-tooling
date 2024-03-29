from typing import List, Optional

class Tool:
    class Function:
        class Operation:
            def __init__(self, uri: str, term: str):
                self.uri = uri
                self.term = term
        
        def __init__(self, operation: List['Tool.Function.Operation']):
            self.operation = operation

    class Topic:
        def __init__(self, uri: str, term: str):
            self.uri = uri
            self.term = term

    class Publication:
        def __init__(self, doi: str, pmid: str, pmcid: str):
            self.doi = doi
            self.pmid = pmid
            self.pmcid = pmcid

    class Credit:
        def __init__(self, name: str, email: str, typeEntity: str):
            self.name = name
            self.email = email
            self.typeEntity = typeEntity

    def __init__(self, data):
        self.name = data['name']
        self.description = data['description']
        self.homepage = data['homepage']
        self.function = [Tool.Function(func) for func in data['function']]
        self.topic = [Tool.Topic(topic) for topic in data['topic']]
        self.language = data['language']
        self.license = data['license']
        self.publication = [Tool.Publication(pub) for pub in data['publication']]
        self.credit = [Tool.Credit(cred) for cred in data['credit']]
        self.confidence_flag = data['confidence_flag']
        self.editPermission = data['editPermission']
        self.biotoolsID = data['biotoolsID']
        self.tool_link = data['tool_link']
        self.publication_link = data['publication_link']
        self.is_preprint = data['is_preprint']
        self.link = data.get('link') 