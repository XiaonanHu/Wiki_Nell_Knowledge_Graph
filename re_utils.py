import re
# =============================================================================
#                   Regular Expressions
# =============================================================================

findTopic = re.compile('>(.*)<')
findAlias = re.compile('\(.*\)')
findAlias2 = r'(title=)(?:(?=(\\?)).)*?(>)'
findAlias3 = r"(href=\"/wiki/Outline_of)(?:(?=(\\?)).)*?(\")"
findSubfield = r"( class=\"mw-headline\" id=\")(?:(?=(\\?)).)*?(\">)"
findLink = r"( href=\"\/wiki\/)(?:(?=(\\?)).)*?(\")"
findBrackets = re.compile(".*?(<.*?>)")
findBrackets = r".*?(<.*?>)"