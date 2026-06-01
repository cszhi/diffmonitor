from flask import request, jsonify, abort

from diffmonitor import app, db
from diffmonitor.models import Diff, DiffRecord
from datetime import datetime
import json
import base64
import os

'''
#将查询结果对象列表转换为指定格式的字典
'''
def dict_helper(objlist):
    result2 = [item.obj_to_dict() for item in objlist]
    return result2


def require_api_token():
    api_token = os.getenv('API_TOKEN')
    if not api_token:
        return

    request_token = request.headers.get('X-API-Token')
    if request_token != api_token:
        abort(401)


def require_form(*fields):
    values = {}
    for field in fields:
        value = request.form.get(field)
        if value is None:
            abort(400, description='missing parameter: {}'.format(field))
        values[field] = value
    return values


@app.before_request
def check_api_token():
    if request.path.startswith('/api/'):
        require_api_token()


@app.route('/api/create', methods=['POST'])
def api_create():
    form = require_form('hostname', 'type', 'md5', 'ip', 'content')

    hostname = form['hostname']
    type = form['type']
    md5 = form['md5']
    ip = form['ip']
    content = form['content']
    now = datetime.now()

    diff = Diff(
        hostname=hostname,
        type=type,
        ip=ip,
        md5=md5,
        content=content,
        created_at=now,
        updated_at=now
    )
    db.session.add(diff)
    db.session.commit()

    diffrecord = DiffRecord(
        hostname=hostname,
        type=type,
        ip=ip,
        md5=md5,
        content=content,
        action='create',
        created_at=now
    )
    db.session.add(diffrecord)
    db.session.commit()

    return "create {} {} success. ".format(hostname, type)


@app.route('/api/md5', methods=['POST'])
def api_md5():
    form = require_form('hostname', 'type', 'md5')

    hostname = form['hostname']
    type = form['type']
    md5 = form['md5']

    diff = Diff.query.filter(Diff.hostname == hostname, Diff.type == type).first()
    now = datetime.now()

    if diff:
        if diff.newmd5 == md5:
            return 'status_no_ok'

        if diff.md5 == md5 and diff.status != 0:
            diff.newmd5 = ""
            diff.newcontent = ""
            diff.diff = ""
            diff.status = 0
            diff.updated_at = now
            db.session.commit()

            diffrecord = DiffRecord(
                hostname=diff.hostname,
                type=diff.type,
                ip=diff.ip,
                md5=diff.md5,
                content=diff.content,
                action='recovery',
                created_at=now
            )
            db.session.add(diffrecord)
            db.session.commit()

        return diff.md5

    return 'null'


@app.route('/api/content', methods=['POST'])
def api_content():
    form = require_form('hostname', 'type')

    diff = Diff.query.filter(
        Diff.hostname == form['hostname'],
        Diff.type == form['type']
    ).first()

    return diff.content if diff else ''


@app.route('/api/update', methods=['POST'])
def api_update():
    form = require_form('hostname', 'type', 'newmd5', 'newcontent', 'diff')

    hostname = form['hostname']
    type = form['type']
    newmd5 = form['newmd5']
    newcontent = form['newcontent']
    diffcontent = form['diff']

    now = datetime.now()
    diff = Diff.query.filter(Diff.hostname == hostname, Diff.type == type).first()

    if diff:
        diff.newmd5 = newmd5
        diff.newcontent = newcontent
        diff.diff = diffcontent
        diff.updated_at = now
        diff.status = 3
        db.session.commit()

        diffrecord = DiffRecord(
            hostname=hostname,
            type=type,
            newmd5=newmd5,
            newcontent=newcontent,
            diff=diffcontent,
            ip=diff.ip,
            md5=diff.md5,
            content=diff.content,
            action='change',
            created_at=now
        )

        db.session.add(diffrecord)
        db.session.commit()
        return "update {} {} success. ".format(hostname, type)

    return ''


@app.route('/api/abnormal')
def api_abnormal():
    diff = Diff.query.with_entities(
        Diff.hostname,
        Diff.type
    ).filter(Diff.status == 3).all()

    return str(diff) + '\n'
