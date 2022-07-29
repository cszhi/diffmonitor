from flask import request,jsonify

from diffmonitor import app, db
from diffmonitor.models import Diff, DiffRecord
from datetime import datetime
import json
import base64

'''
#将查询结果对象列表转换为指定格式的字典
'''
def dict_helper(objlist):
    result2 = [item.obj_to_dict() for item in objlist]   # 获取类自定义字典转换函数，转换为字典列表
    return result2

@app.route('/api/create', methods=['POST'])
def api_create():
    hostname = request.form['hostname']
    type = request.form['type']
    md5 = request.form['md5']
    ip = request.form['ip']
    content = request.form['content']
    now = datetime.now()

    #创建记录
    diff = Diff(
        hostname=hostname,
        type=type,
        ip=ip,
        md5=md5,
        content=content,
        created_at = now,
        updated_at = now
    )
    db.session.add(diff)
    db.session.commit()

    #创建历史监控记录
    diffrecord = DiffRecord(
        hostname=hostname,
        type=type,
        ip=ip,
        md5=md5,
        content=content,
        action='create',
        created_at = now
    )
    db.session.add(diffrecord)
    db.session.commit()

    return "create "+hostname+" "+type+" success. "

@app.route('/api/md5', methods=['POST'])
def api_md5():
    hostname = request.form['hostname']
    type = request.form['type']
    md5 = request.form['md5']
    diff = Diff.query.filter(Diff.hostname == hostname, Diff.type == type).first()
    now = datetime.now()

    if diff:
        if diff.newmd5 == md5:
            return 'status_no_ok'
        
        #自动恢复
        if diff.md5 == md5 and diff.status !=0:
            diff.newmd5 = ""
            diff.newcontent = ""
            diff.diff = ""
            diff.status = 0
            diff.updated_at = now
            db.session.commit()

            #创建自动恢复历史记录
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
    hostname = request.form['hostname']
    type = request.form['type']

    diff = Diff.query.filter(Diff.hostname == hostname, Diff.type == type).first()
    
    return diff.content if diff else ''

@app.route('/api/update', methods=['POST'])
def api_update():
    hostname = request.form['hostname']
    type = request.form['type']
    newmd5 = request.form['newmd5']
    newcontent = request.form['newcontent']
    diffcontent = request.form['diff']
    now = datetime.now()
    diff = Diff.query.filter(Diff.hostname == hostname, Diff.type == type).first()

    if diff:
        #更新
        diff.newmd5 = newmd5
        diff.newcontent = newcontent
        diff.diff = diffcontent
        diff.updated_at = now
        diff.status = 3
        db.session.commit()

        #创建历史记录
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
        return "update "+hostname+" "+type+" success. "

    return ''

@app.route('/api/abnormal')
def api_abnormal():
    diff = Diff.query.with_entities(Diff.hostname,Diff.type).filter(Diff.status == 3).all()
    return str(diff)+'\n'
    #return jsonify(dict_helper(diff)) if diff else ''