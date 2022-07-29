from flask import render_template, request, url_for, redirect, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import text

from diffmonitor import app, db
from diffmonitor.models import User, Diff, DiffRecord
from datetime import datetime

import os
import sys

@app.route('/diff/')
@app.route('/')
@login_required
def diff():
    hostname = request.args.get('hostname')
    type = request.args.get('type')
    page_size = int(request.args.get('page_size')) if request.args.get('page_size') else 15

    all_filters = []
    if hostname:
        all_filters.append(Diff.hostname.like("{}%".format(hostname)))
    if type:
        all_filters.append(Diff.type == type)

    search = True if hostname or type else False
    display_msg = '展示 {start}-{end} , 总共 {total}'
    page = int(request.args.get('page', 1))

    if search:
        paginate = Diff.query.filter(*all_filters).order_by(text("status desc, created_at desc")).paginate(page=page, per_page=page_size, error_out=False)
    else:
        paginate = Diff.query.order_by(Diff.status.desc(), Diff.updated_at.desc()).paginate(page=page, per_page=page_size, error_out=False)

    diffs = paginate.items

    pagination = Pagination(page=page, total=paginate.total, per_page=page_size, display_msg=display_msg)
    
    return render_template('diff.html', diffs=diffs, pagination=pagination, page='diff', hostname=hostname, type=type, page_size=page_size)

@app.route('/diff/show/<int:diff_id>')
@login_required
def diff_show(diff_id):
    diff = Diff.query.get_or_404(diff_id)
    return jsonify(diff.obj_to_dict())

@app.route('/diff/confirm/<int:diff_id>', methods=['POST'])
@login_required
def diff_confirm(diff_id):
    comment = request.form['comment']
    status = request.form['status']
    if not comment or not status:
            flash('输入无效.', 'error')
            return redirect(url_for('diff_confirm'))
    now = datetime.now()
    #return status
    if status == '0':  
        action = "reset"
    elif status == '1':
        action = "process"

    diff = Diff.query.get_or_404(diff_id)
    #正常状态不处理
    if diff.status == 0:
        flash('已经是正常状态.', 'info')
        return redirect(request.referrer)

    md5 = diff.md5
    newmd5 = diff.newmd5
    content = diff.content
    newcontent = diff.newcontent
    hostname = diff.hostname
    type = diff.type
    ip = diff.ip
    diffdiff = diff.diff

    #从异常状态标记为正常状态
    if status == '0':
        diff.md5 = newmd5
        diff.content = newcontent
        diff.newmd5 = ""
        diff.newcontent = ""
        diff.diff = ""
    
    #从处理中状态标记为正常状态只需修改status和updated_at
    diff.status = status 
    diff.updated_at = now
    db.session.commit()

    #添加记录到历史记录表
    if status == '0':
        diffrecord = DiffRecord(
            hostname=hostname,
            type=type,
            ip=ip,
            md5=md5,
            content=content,
            action=action,
            comment=comment,
            diff=diffdiff,
            created_at = now,
            username=current_user.username
        )
    elif status == '1':
        diffrecord = DiffRecord(
            hostname=hostname,
            type=type,
            ip=ip,
            md5=md5,
            newmd5=newmd5,
            content=content,
            newcontent=newcontent,
            action=action,
            comment=comment,
            diff=diffdiff,
            created_at = now,
            username=current_user.username
        )

    db.session.add(diffrecord)
    db.session.commit()
    flash('标记成功.', 'success')
    return redirect(request.referrer)

@app.route('/diff/batchconfirm/', methods=['POST'])
@login_required
def diff_batch_confirm():
    comment = request.form['comment']
    status = request.form['status']
    checked = request.form['ids']
    if not checked:
        flash('未选中任何记录.', 'error')
        return redirect(request.referrer)
        
    checked = checked.split(' ')
    checked.pop()
    
    if not comment or not status:
            flash('输入无效.', 'error')
            return redirect(url_for('diff_confirm'))
    now = datetime.now()
    #return status
    if status == '0':  
        action = "reset"
    elif status == '1':
        action = "process"

    for i in checked:
        diff = Diff.query.get_or_404(i)
        #正常状态不处理
        if diff.status == 0:
            continue
        md5 = diff.md5
        newmd5 = diff.newmd5
        content = diff.content
        newcontent = diff.newcontent
        hostname = diff.hostname
        type = diff.type
        ip = diff.ip
        diffdiff = diff.diff

        #从异常状态标记为正常状态
        if status == '0':
            diff.md5 = newmd5
            diff.content = newcontent
            diff.newmd5 = ""
            diff.newcontent = ""
            diff.diff = ""

        #从处理中状态标记为正常状态只需修改status和updated_at
        diff.status = status 
        diff.updated_at = now
        db.session.commit()

        #添加记录到历史记录表

        if status == '0':
            diffrecord = DiffRecord(
                hostname=hostname,
                type=type,
                ip=ip,
                md5=md5,
                content=content,
                action=action,
                comment=comment+" - 批量操作",
                diff=diffdiff,
                created_at = now,
                username=current_user.username
            )
        elif status == '1':
            diffrecord = DiffRecord(
                hostname=hostname,
                type=type,
                ip=ip,
                md5=md5,
                newmd5=newmd5,
                content=content,
                newcontent=newcontent,
                action=action,
                comment=comment+" - 批量操作",
                diff=diffdiff,
                created_at = now,
                username=current_user.username
            )
        db.session.add(diffrecord)
        db.session.commit()
    flash('批量标记成功.', 'success')
    return redirect(request.referrer)

@app.route('/diff/delete/<int:diff_id>', methods=['POST'])
@login_required
def diff_delete(diff_id):
    diff = Diff.query.get_or_404(diff_id)
    db.session.delete(diff)
    db.session.commit()
    flash('删除成功.', 'success')
    return redirect(request.referrer)

@app.route('/diff/batchdelete', methods=['POST'])
@login_required
def diff_batch_delete():
    checked = request.form['ids']
    if not checked:
        flash('未选中任何记录.', 'error')
        return redirect(request.referrer)
        
    checked = checked.split(' ')
    checked.pop()
    for i in checked:
        diff = Diff.query.get_or_404(i)
        db.session.delete(diff)
        db.session.commit()
    flash('批量删除成功.', 'success')
    return redirect(request.referrer)

@app.route('/diffrecord/')
@login_required
def diff_record():
    
    hostname = request.args.get('hostname')
    type = request.args.get('type')
    page_size = int(request.args.get('page_size')) if request.args.get('page_size') else 15
    all_filters = []
    if hostname:
        all_filters.append(DiffRecord.hostname.like("{}%".format(hostname)))
    if type:
        all_filters.append(DiffRecord.type == type)

    search = True if hostname or type else False 
    display_msg = '展示 {start}-{end} , 总共 {total}'
    page = int(request.args.get('page', 1))

    if search:
        paginate = DiffRecord.query.filter(*all_filters).order_by(DiffRecord.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)
    else:
        paginate = DiffRecord.query.order_by(DiffRecord.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)

    diffs = paginate.items
    pagination = Pagination(page=page, total=paginate.total, per_page=page_size, display_msg=display_msg)
    
    return render_template('diffrecord.html', diffs=diffs, pagination=pagination, page='diffrecord', hostname=hostname, type=type, page_size=page_size)

@app.route('/diffrecord/show/<int:id>')
@login_required
def diff_record_show(id):
    diff_record = DiffRecord.query.get_or_404(id)
    return jsonify(diff_record.obj_to_dict())

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']

        if len(password) < 6 or not password_confirmation or password != password_confirmation:
            flash('输入密码无效.', 'error')
            return redirect(url_for('settings'))

        user = User.query.filter(User.username == current_user.username).first_or_404()
        user.set_password(password)
        db.session.commit()
        flash('设置成功.', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', page='settings')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter(User.username == username).first()
        if not user:
            flash('用户不存在.', 'error')
            return render_template('login.html', username=username)

        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('登录成功.', 'success')
            return redirect(url_for('diff'))

        flash('密码错误.', 'error')
        return render_template('login.html', username=username)

    return render_template('login.html', page='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('再见.', 'success')
    return redirect(url_for('diff'))
