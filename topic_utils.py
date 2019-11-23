# =============================================================================
#                   Classes for topics and links
# =============================================================================
class Topic:
    def __init__(self, name, alias, wiki):
        self.name = name
        self.alias = alias
        self.wiki = wiki
        self.wiki_name = None
        self.summary = None
    def add_wiki_name(self, wiki_name):
        self.wiki_name = wiki_name
        
        
class Relation:
    def __init__(self, parent, child):
        self.parent = parent
        self.child = child
        self.relation = None
        self.childSummary = None
        self.childLink = None
        self.childAliases = None