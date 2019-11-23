import urllib.request,urllib
import re, csv, copy
from bs4 import BeautifulSoup
import importlib
import nltk
from topic_utils import *

# =============================================================================
#                   Expand the database using NELL database
# =============================================================================

def get_topics_from_nell():

    file = open("bkisiel_aaai10_08m.100.SSFeedback.csv",'r')
    topic_list, score_list = [], []

    with file as csvfile:
        filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')

        for row in filereader:
            line = ', '.join(row)

            # Extract only academicfield names in the knowledge base
            if 'academicfield' in line and 'rights' not in line:
                line = row[0].split('\t')
                del line[1]

                if  float(line[3])>0.95 and not bool(re.search(r'\d', line[1])):
                    topic = ' '.join(x for x in line[1].split('_'))
                    
                    if topic.lower() not in topic_list:
                        topic_list.append(Topic(topic.lower(), None, ""))
                        score_list.append(line[3])     

    return topic_list, score_list

