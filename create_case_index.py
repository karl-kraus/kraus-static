#!/usr/bin/env python
# coding: utf-8

import glob
import json
from acdh_tei_pyutils.tei import TeiReader
from dateutil.parser import parse

files = glob.glob('./data/cases_tei/C*.xml')
tei_ns = {'tei': "http://www.tei-c.org/ns/1.0"}
faulty = []
cases = []
class_codes = {}
keywords = []
persons = {}
roles = {}


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def date_from_tei(path_to_file, default=""):
    """
    Tries to extract some iso-date from the passed in doc

    :param path_to_file: str, path the TEI-Doc
    :param default: str; a default value to be returned in case no useful date could be found
    """
    try:
        doc = TeiReader(path_to_file)
    except Exception as e:
        print(e)
        return default
    try:
        date_el = doc.any_xpath('.//tei:creation/tei:date')[0]
    except IndexError:
        print(path_to_file)
        return default
    date_attr = date_el.attrib.items()
    try:
        date = [x[1] for x in date_attr if is_date(x[1])][0]
    except IndexError:
        return default
    return date.strip()


for x in files:
    try:
        doc = TeiReader(x)
    except Exception as e:
        faulty.append([x, e])
    case = {}
    case['id'] = doc.any_xpath('./@xml:id')[0]
    case['title'] = doc.any_xpath('.//tei:title/text()')[0]
    case['docs'] = [x.text for x in doc.any_xpath('.//tei:list[1]/tei:item/tei:ref')]
    case['docs_count'] = len(case['docs'])
    case['keywords'] = []
    for t in doc.any_xpath('.//tei:term/text()'):
       case['keywords'].append(t)
       keywords.append(t)
    for c in doc.any_xpath('.//tei:classCode'):
        cc = {}
        cc['id'] = c.attrib['scheme']
        cc['label'] = c.text
        class_codes[c.attrib['scheme']] = c.text
    actors = []
    for a in doc.any_xpath('.//tei:person[@role]'):
        actor = {}
        actor['id'] = a.xpath('./@ref')[0]
        actor['title'] = a.xpath('./tei:persName/text()', namespaces=tei_ns)[0]
        actor['role_id'] = a.xpath('@role', namespaces=tei_ns)[0]
        actor['role_label'] = a.xpath('./tei:ab/text()', namespaces=tei_ns)[0] 
        actors.append(actor)
        persons[actor['id']] = actor['title']
        roles[actor['role_id']] = actor['role_label']
    case['actors'] = actors
    case['actor_count'] = len(actors)
    try:
        case['first_doc'] = case['docs'][0]
        case['last_doc'] = case['docs'][-1]
    except IndexError:
        case['first_doc'] = ""
        case['last_doc'] = ""
    case['start_date'] = date_from_tei(f"./data/editions/{case['first_doc']}")
    case['end_date'] = date_from_tei(f"./data/editions/{case['last_doc']}", default='')
    cases.append(case)
data = {
    'cases': cases,
    'persons': persons,
    'roles': roles,
    'keywords': list(set(keywords)),
    'class_codes': class_codes
}
with open('cases-index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
