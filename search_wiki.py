
import urllib.request,urllib
import re, csv, copy
from bs4 import BeautifulSoup
import importlib
import nltk

from re_utils import *
from topic_utils import *


# =============================================================================
#                   Helper functions
# =============================================================================

def check_valid_topic(topic):

    if len(topic) and len(topic[0]) > 3 and not 'Wikipedia' in topic[0] \
       and not 'wikipedia' in topic[0] and not '<abbr' in topic[0] \
       and not '</span>' in topic[0] and not 'Portal' in topic[0] \
       and not 'portal' in topic[0] and not 'Content Listings' in topic[0]\
       and not 'Shortcuts' in topic[0] and not 'Disclaimers' in topic[0] \
       and not 'Spoken articles' in topic[0] and not 'Content listings' in topic[0]\
       and not 'Overviews' in topic[0] and not 'Reference' in topic[0] \
       and not 'A-Z' in topic[0] and not 'a-z' in topic[0] \
       and not '<span>' in topic[0] and not '<a class' in topic[0] \
       and not '<a href="/w/index.php?' in topic[0] and not '—&#160;' in topic[0] \
       and not 'all pages beginning with' in topic[0] :
        return True
    return False


def get_topic_name(text):
    """
    Taken from: https://stackoverflow.com/questions/15175142/how-can-i-do-multiple-substitutions-using-regex-in-python?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    """
    replace_dict = {
      "<b>" : "", "</b>" : "", "<i>" : "", "</i>": "", "<sub>": "-", "</sub>": "",
      "<a>" : "", "</a>" : "", "</a> " : "", "</li>": "", "<sup>#</sup>": "",
      "<sup>#": "", "<sup>‡</sup>": "", "&#8211":"", "</ul>": "", "&#160":"",
      "<sup>":"", ")<":""
  }   

    # First round of filtering
    if '</a>' in text: cleaned_text = text[:text.index('</a>')]
    else: cleaned_text = text
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, replace_dict.keys())))
    cleaned_text = regex.sub(lambda mo: replace_dict[mo.string[mo.start():mo.end()]], cleaned_text) 
    stop_points = [', <a href="', ' - ', ' – ', ' (<a href',' (', '• <a ', '/', ' and <a href="', ' ; ',
                  ';(<a href="', '– <a href="', ' -- <a href="', ' / <a href="',
                  ': <a href="', '/<a href="', ', a <a href="', ';<a href="',
                  ' <a href="', ';<span class="', '<sup id="', ') {<a href="',\
                  '(<a href="', "<"]

    for brk in stop_points:
        if brk in cleaned_text:
            cleaned_text = cleaned_text[:cleaned_text.index(brk)]
    return cleaned_text


def change_name(name, cur_parents, h, depth): # change wiki names into Learn Anything names

    if h == 'h2':
        discipline = cur_parents[0]
        if name == "see also": 
            name = "related topic of " + discipline
            depth = 2
        elif name == "external links": 
            name = "other resource of " + discipline
            depth = 2
        elif name == "lists":
            name = "lists with topics related to " + discipline
        elif name == "other fields":
            name = "other fields related to " + discipline
        elif name == "applications":
            name = "applications of " + discipline
        elif name == "use":
            name = "use of " + discipline
        elif nltk.pos_tag(name.split())[0][1] == "IN":
            name = discipline + " " + name
            
    return name, depth


def get_topic_summary(line):

    matches = re.findall(findBrackets, line)

    for m in matches:
        ind = line.index(m)
        line = line[:ind] + line[ind+len(m):]

    return line


def get_discipline_name(line):
    
    if 'Outline_of' in line: # wiki name
        matches = re.finditer(findAlias3, line)

        if 'href' in line:
            wiki_name = list(line[match.start()+12:match.end()-1] for match in matches)
        else: wiki_name = None 

        return wiki_name

    else: return None


def get_topic_alias(line):

    if '(' in line or ' / ' in line:

        if 'title=' in line:
            matches = re.finditer(findAlias2, line)
            alias = list(line[match.start()+7:match.end()-2] for match in matches)
        else:

            if '(' in line:
                alias = list(x[1:-1] for x in re.findall(findAlias, line))
            elif ' / ' in line:
                alias = line.split(' / ')[1:]

        return alias
    else:
        return None


def get_topic_link(line):

    matches = re.finditer(findLink, line)
    links = list(line[match.start()+12:match.end()-1] for match in matches)
    link = "https://en.wikipedia.org/wiki" + links[0]    

    return link


def get_discipline_info(topic, link, line):

    d = get_topic_name(topic[0]).lower()
    if not len(d): return None
    
    if 'outline of ' in d: d = re.sub('outline of ', '', d)
    
    alias = get_topic_alias(topic[0])
    wiki_name = get_discipline_name(line)
    discipline = Topic(d, alias, link)
    discipline.add_wiki_name(wiki_name)
    
    return discipline


def get_topic_info(topic, wiki):

    t_name = get_topic_name(topic[0]).lower()
    if t_name == "knowledge that is":
        print('t_name KNOWLEDGE THAT IS ',topic[0])    
    t = topic[0]
    
    alias = get_topic_alias(t)
    
    return Topic(t_name, alias, wiki)



# =============================================================================
#                   Expand the database using Wikipedia
# =============================================================================        
def link_to_subfield(line, cur_parents, depth, h):

    matches = re.finditer(findSubfield, line)
    subfield = list(line[match.start()+25:match.end()-2] for match in matches)
    # Do not care about titles such as "what type of thing is computer science?"
    if len(subfield) and '?' not in subfield[0]: 
        subfield = re.sub("_", " ", subfield[0].lower())
        subfield, depth = change_name(subfield, cur_parents, h, depth)
        if 'by' in subfield and 'b' == subfield[0]:
            subfield = cur_parents[int(h[1])-2] + subfield
        cur_parents[int(h[1])-1] = subfield 
        r = Relation(cur_parents[int(h[1])-2], subfield)
        
        if ' href="/wiki/' in line:
            r.childLink = get_topic_link(line)     
        if ' – ' in line: 
            r.childSummary = get_topic_summary(line[line.index(' – ')+3:])
        r.childAliases = get_topic_alias(line)

        return r, int(h[1])-1 # return 

    else: return None, depth


def line_contains_topic(line):

    has_topic = ('<li>' in line) or (' href="/wiki/' in line)
    if '<div' not in line and '<p>' not in line and has_topic:
        return True
    else: 
        return False
    

def get_topic_with_url(line):
    
    link = get_topic_link(line)
    start = line.index(' href="/wiki/')
    topic = re.findall(findTopic, line[start:])
    
    return topic, link


def get_topic_without_url(line):

    if '<li>' in line:
        start = line.index('<li>')+4
        if '</li>' in line: end = line.index('</li>')
        else: end = len(line)
        return [line[start:end]] # need to be a list 

    else:
        return None



# =============================================================================
#                   Main functions
# =============================================================================

def get_new_topics_from_disciplines(d): 
    '''
    Get topics from course discipline 'd'
    '''

    if d.wiki_name != None and len(d.wiki_name):
        link = "https://en.wikipedia.org/wiki/" + d.wiki_name[0]
    else:
        link = "https://en.wikipedia.org/wiki/Outline_of_" + re.sub(' ', '_', d.name)

    discipline = d.name
    topic_list = []
    discipline_list = []    

    try:
        f = urllib.request.urlopen(link)

    except UnicodeEncodeError as err:
        return None

    except urllib.error.HTTPError as err:
        link = "https://en.wikipedia.org/wiki/" + re.sub(' ', '_', d.name)

        try:
            f = urllib.request.urlopen(link)
        except (urllib.error.HTTPError, UnicodeEncodeError) as err:
            return None
        
    lines = f.read().decode('utf-8').split('\n')
    subfield, subfieldtopic = "", ""
    relation_list, depth = [], 1
    cur_parents = ["" for _ in range(20)] 
    cur_parents[0] = discipline
    
    for line in lines:
        h_levels = ['h2', 'h3', 'h4', 'h5', 'h6']
        has_h = list(h in line for h in h_levels)
        
        if True in has_h: # If topic contains subfields
            h_idx = h_levels[has_h.index(True)]
            r, depth = link_to_subfield(line, cur_parents, depth, h_idx)
            if r: relation_list.append(r)

        # one level deeper 
        if cur_parents[1] != "" and '<ul>' in line: depth += 1
        
        # nodes without h, can extend to multiple depths as well
        if cur_parents[1] != "" and line_contains_topic(line): 
            has_url = ' href="/wiki/' in line

            if has_url: topic, link = get_topic_with_url(line)
            else: topic = get_topic_without_url(line)
            
            # Reaching the end 
            if len(topic) and subfield != "" and "<abbr " in topic[0]: break

            if ('Resources' in line and '<li>' not in line) or 'external text' in line: break
            
            if check_valid_topic(topic): 
                child = get_topic_name(topic[0]).lower()
                cur_parents[depth] = child
                
                if cur_parents[depth-1] != "": # If topic has parent
                    r = Relation(cur_parents[depth-1],child)

                    if has_url:  r.childLink = link

                    if ' – ' in topic[0]:
                        r.childSummary = get_topic_summary(topic[0][topic[0].index(' – ')+3:])
                    r.childAliases = get_topic_alias(topic[0])
                    relation_list.append(r)
                    
            else: pass
            
        # one level higher
        if cur_parents[1] != "" and '</ul>' in line: 
            depth -= line.count('</ul>')  
        
    return relation_list


def expand_discipline_list(d_list_orig):

    d_list = copy.deepcopy(d_list_orig)
    discipline_names = list(d.name for d in d_list)
    link = "https://en.wikipedia.org/wiki/Portal:Contents/Outlines"
    f = urllib.request.urlopen(link)
    lines = f.read().decode('utf-8').split('\n')  
    stp = False # starting point

    for line in lines:
        if 'Culture_and_the_arts_' in line: stp = True
        
        if stp: # we start to process after starting point

            if ' href="/wiki/' in line:
                
                link = get_topic_link(line)
                start = line.index(' href="/wiki/')
                topic = re.findall(findTopic, line[start:])
                
                if check_valid_topic(topic):  
                    d = get_discipline_info(topic, link, line)

                    if not d: continue
                    else:
                        
                        if d.name not in discipline_names: 
                            if  '<i>' not in d.name:
                                d_list.append(d)
                                discipline_names.append(d.name)
                        
    return d_list


def get_topics_from_wiki():
    topic_list = []
    discipline_list = []    
    link = "https://en.wikipedia.org/wiki/Outline_of_academic_disciplines"
    f = urllib.request.urlopen(link)
    lines = f.read().decode('utf-8').split('\n')

    for line in lines:

        if ' href="/wiki/' in line:
            wiki = get_topic_link(line)
            start = line.index(' href="/wiki/')
            topic = re.findall(findTopic, line[start:])

            if check_valid_topic(topic): 

                if 'Outline of' in topic[0]: # If the topic is a discipline
                    discipline_list.append(get_discipline_info(topic, wiki, line))
                else: # If the topic is not a discipline
                    topic_list.append(get_topic_info(topic, wiki))
    
    discipline_list = list(set(discipline_list))
    topic_list = list(set(topic_list))
            
    return discipline_list, topic_list
