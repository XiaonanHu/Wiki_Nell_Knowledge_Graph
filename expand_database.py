
import json, re, pprint, copy, datetime
from search_nell import get_topics_from_nell
from search_wiki import get_topics_from_wiki, get_new_topics_from_disciplines, expand_discipline_list
from topic_utils import Topic, Relation

# Load the original json data and store them into a dictionary
with open('topics.json', encoding='utf-8-sig') as topics_data:
    topics = json.load(topics_data)
with open('resources.json', encoding='utf-8-sig') as resources_data:
    resources = json.load(resources_data)
# parents and children must be topics 
with open('links-rel.json', encoding='utf-8-sig') as links_data:
    links = json.load(links_data)
# parents must be topics and children must be resources
with open('children-rel.json', encoding='utf-8-sig') as children_data:
    children = json.load(children_data)


class Topics:
    def __init__(self):
        self.topic_by_name = {}
        self.topic_by_ID = {}
        self.topic_name_list = []
        self.topic_list = []  
        self.max_id = 0
        
    def add_topic(self,topic):
        self.topic_by_name[topic["name"]] = topic
        self.topic_by_ID[topic["nodeID"]] = topic
        self.topic_list.append(topic)
        self.topic_name_list.append(topic["name"])
        
    def find_by_name(self,name):
        if name in self.topic_by_name.keys():
            return self.topic_by_name[name]
        else: return None
        
    def find_by_ID(self,ID):
        if ID in self.topic_by_ID.keys():
            return self.topic_by_ID[ID]
        else: return None
        
    def get_topic_names(self):
        return self.topic_name_list
    
    def intialize_max_ID(self):
        self.max_id = get_largest_ID_num([topics,children]) + 1
        
    def get_new_ID(self):
        self.max_id += 1
        return self.max_id - 1
    
    def get_cur_ID(self):
        return self.max_id



def get_largest_ID_num(total_list):

    max_id = 0
    for dict_list in total_list:
        max_list = []

        for dictionary in dict_list:
            id_list = list(value for key,value in dictionary.items() if 'ID' in key)

            if None in id_list: print(id_list)

            if len(id_list) > 0: 
                max_val = max(id_list)
                max_list.append(max_val)

        if max(max_list) > max_id: max_id = max(max_list)
        
    return max_id


def update_link_list(T,d_list):
    # Read in existing links
    new_links = copy.deepcopy(links)
    r_list = []
    for d in d_list:
        r = get_new_topics_from_disciplines(d)
        if r != None:
            r_list += r
    
    for r in r_list: # for each relation
        parent, child = r.parent, r.child
        tp = T.find_by_name(parent)
        tc = T.find_by_name(child)
        exist = True
        if not tp: # parent does not exist
            #print('cannot find parent',parent)
            parentID = T.get_new_ID()
            tp = {"name":parent, "nodeID":parentID, "wiki":None, "summary":None}
            T.add_topic(tp)
            exist = False
        else: parentID = tp["nodeID"]

        if not tc: # child does not exist
            childID = T.get_new_ID()
            tc = {"name":child, "nodeID":childID, "wiki":r.childLink, "summary":r.childSummary}
            T.add_topic(tc)   
            exist = False
        else: childID = tc["nodeID"]
        
        if exist:

            childList = list(x["childID"] for x in new_links if x["parentID"] == tp["nodeID"])
            if childID not in childList:
                new_links.append({"parentID":parentID, "childID":childID})

        else:
            new_links.append({"parentID":parentID, "childID":childID})
                
    return T,new_links,r_list


    
def update_topic_list():
    # Initialize and retrieve all the existing topics
    T = Topics()
    for topic in topics:
        topic["name"] = topic["name"].lower()
        T.add_topic(topic)
    T.intialize_max_ID()
    
    # Add topics from Nell dataset
    t_list, s_list = get_topics_from_nell()
    curID = T.get_new_ID()
    add_list,exist_list = [],[]
    for t in t_list:
        if t.name not in T.get_topic_names():
            topic = {"name":t.name,"nodeID":curID,"wiki":None,"summary":None}
            T.add_topic(topic)
            curID = T.get_new_ID()

    # Add topics from Wiki
    d_list, t_list = get_topics_from_wiki()
    for d in d_list:
        print(d.name,d.alias)

    for t in t_list:
        if t.name not in T.get_topic_names():
            if t.alias:
                topic = {"name":t.name,"nodeID":curID,"wiki":t.wiki,"summary":None,"aliases":t.alias}
            else:
                topic = {"name":t.name,"nodeID":curID,"wiki":t.wiki,"summary":None}
            T.add_topic(topic)
            curID = T.get_new_ID()
        else:
            topic = T.find_by_name(t.name)

    # Add topics related to the disciplines from wiki
    for d in d_list:
        if d.name not in T.get_topic_names():
            if d.alias:
                topic = {"name":d.name,"nodeID":curID,"wiki":d.wiki,"summary":None,"aliases":d.alias}
            else:
                topic = {"name":d.name,"nodeID":curID,"wiki":d.wiki,"summary":None}
            T.add_topic(topic)
            curID = T.get_new_ID()
        else:
            topic = T.find_by_name(d.name)

    return T, d_list



def append_extra(d_list):
    if 'machine learning' not in d_list: 
        d_list.append(Topic('machine learning',['Outline_of_machine_learning'],None))
    d_list.append(Topic('quantum theory', ['List_of_mathematical_topics_in_quantum_theory'],None))
    d_list.append(Topic('topology', ['List_of_general_topology_topics'],None))
    d_list.append(Topic('genetic genealogy',['List_of_genetic_genealogy_topics'],None))
    
    return d_list

now = datetime.datetime.now()
n1 = len(topics)

T, d_list = update_topic_list()
n2 = len(d_list)
n3 = len(T.topic_list)

d_list2 = expand_discipline_list(d_list)
d_list2 = append_extra(d_list2)
n4 = len(d_list2)

T, new_links,r_list = update_link_list(T,d_list2)
n5 = len(T.topic_list)

print('\ntopic # initially:', n1)
print('topics # after Nell and Wiki:', n3)
print()
print('discipline # original', n2)
print('discipline new', n4)
print('topics # after updating discipline connections from Wiki:',n5)
print()
print('links # initially:',len(links))
print('links # after updating discipline connections from wiki:',len(new_links))


jdata = json.dumps(T.topic_list)
parsed = json.loads(jdata)
topicFileName = "topics-"+str(now).split()[0] + ".json"
with open(topicFileName,'w') as f:
    json.dump(parsed, f, indent=4)
    
linkFileName = "links-"+str(now).split()[0] + ".json"
jdata = json.dumps(new_links)
parsed = json.loads(jdata)
with open(linkFileName,'w') as f:
    json.dump(parsed,f,indent=4)
