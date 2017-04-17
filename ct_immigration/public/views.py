# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from ..cms import get_content
from tinydb import TinyDB, Query

blueprint = Blueprint('public', __name__, static_folder='../static')

db = TinyDB('immigration.json')

def mng_content(cache_duration=900):
    """
    Retrieve the cms content either from the local tinydb instance or the google sheet
    :param cache_duration: integer representing the time in seconds to cache content for. Defaults to 900 seconds.
    :return: list of content items, either from database or sheet
    """
    UPDATE = False
    NEW = False
    now = datetime.datetime.now()
    Content = Query()
    cms_content = db.search(Content.type == 'Content')
    if cms_content == []:
        content = get_content()
        UPDATE = True
        NEW = True
    else:
        ts = datetime.datetime.fromtimestamp(cms_content[0]['timestamp'])
        if (now - ts).seconds >= cache_duration:
            content = get_content()
            UPDATE = True
        else:
            content = cms_content[0]['content']
    if UPDATE:
        if NEW:
            db.insert({'type': 'Content', 'timestamp': now.timestamp(), 'content': content})
        else:
            db.update({'type': 'Content', 'timestamp': now.timestamp(), 'content': content}, Content.type == 'Content')
    return content

@blueprint.route('/', methods=['GET'])
def home():
    """Home page."""
    content = mng_content(cache_duration=900)
    return render_template('public/home.html', content=content)

@blueprint.route('/about/')
def about():
    """About page."""
    return render_template('public/about.html')
