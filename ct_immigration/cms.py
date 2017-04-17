import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

sn = "Migration Data Story Content"
tooltip_regex = re.compile('\(\((.*?)\)\)\[\[(.*?)\]\]')


def is_list(element):
    if element['Content Type'] == 'Bullet List' or element['Content Type'] == 'Ordered List':
        return True
    return False

def is_list_item(element):
    if element['Content Type'] == 'Bullet List Item' or element['Content Type'] == 'Ordered List Item':
        return True
    return False

def fetch_sheet(sheet_name):
    """ 
    Use service_creds.json to create a client to interact with the Google Drive API

    :param sheet_name: name of the google sheet to fetch
    :return: gspread workbook object
    """
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_creds.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    workbook = client.open(sheet_name)

    return workbook


def parse_sheet(record_list):
    """
    Take a list of worksheet record elements stored as dicts and return a structured node list
    :param record_list: list of dicts
    :return: list of dicts
    """
    ON_LIST = False
    content_tree = {'section': '', 'graphic': '', 'items': []}
    current_list = {'type': '', 'list_items': []}
    for el in record_list.get_all_records():
        if is_list(el):
            ON_LIST = True
            if el['Content Type'] == 'Bullet List':
                current_list['type'] = 'Unordered List'
            else:
                current_list['type'] = 'Ordered List'
            try:
                current_list['content'] = el['Content']
            except KeyError:
                current_list['content'] = ''
        elif is_list_item(el):
            current_list['list_items'].append(el['Content'])
        elif el['Content Type'] == 'Graphic':
            content_tree['graphic'] = el['Content']
        elif is_list(el) == False:
            if ON_LIST == True:
                ON_LIST = False
                content_tree['items'].append(current_list)
                current_list = {'type': '', 'list_items': []}
            c = el['Content']
            tooltips = tooltip_regex.search(c)
            if tooltips:
                basetext = tooltips.groups()[0]
                tip = tooltips.groups()[1]
                match_span = tooltips.span()
                tip_element = "<a href='#' data-toggle='tooltip' title='{}'>{}</a>".format(tip, basetext)
                to_replace = c[match_span[0]:match_span[1]]
                el['Content'] = c.replace(to_replace, tip_element)
            else:
                el['Content'] = c
            content_tree['items'].append({'type': el['Content Type'], 'content': el['Content']})

    return content_tree


def build_content_object(workbook):
    """
    Take a gspread workbook object and parse into a node list for template rendering

    :param workbook: A gspread workbook object 
    :return: list of document elements
    """

    # Filter out the instructional sheet and build a lookup so that we can properly parse
    # the document content using the index
    lookup = {s._title: s for s in workbook if s._title != 'Overview and Instructions'}

    # Get the index and build a list of the order in which sheets should be parsed
    index = lookup['Index']
    section_order = [so['Section Order'] for so in index.get_all_records() if so['Section Order'] in lookup]

    content = [parse_sheet(lookup[s]) for s in section_order]
    return content


def get_content():
    worksheet = fetch_sheet(sn)
    return build_content_object(worksheet)
