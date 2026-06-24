from datetime import datetime
from functools import wraps

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_paginate import Pagination

from diffmonitor import app, db
from diffmonitor.models import Diff, DiffRecord, User


BATCH_COMMENT_SUFFIX = ' - 批量操作'


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def _pagination(query, page, page_size):
    return query.paginate(page=page, per_page=page_size, error_out=False)


def _page_size(default=15):
    return int(request.args.get('page_size') or default)


def _selected_ids():
    return [diff_id for diff_id in request.form.get('ids', '').split() if diff_id]


def _status_action(status):
    return {'0': 'reset', '1': 'process'}.get(status)


def _apply_confirm(diff, status, now):
    original = {
        'hostname': diff.hostname,
        'type': diff.type,
        'ip': diff.ip,
        'md5': diff.md5,
        'newmd5': diff.newmd5,
        'content': diff.content,
        'newcontent': diff.newcontent,
        'diff': diff.diff,
    }

    if status == '0':
        diff.md5 = diff.newmd5
        diff.content = diff.newcontent
        diff.newmd5 = ''
        diff.newcontent = ''
        diff.diff = ''

    diff.status = int(status)
    diff.updated_at = now
    return original


def _build_diff_record(original, action, comment, now):
    record_data = {
        'hostname': original['hostname'],
        'type': original['type'],
        'ip': original['ip'],
        'md5': original['md5'],
        'content': original['content'],
        'action': action,
        'comment': comment,
        'diff': original['diff'],
        'created_at': now,
        'username': current_user.username,
    }
    if action == 'process':
        record_data.update({
            'newmd5': original['newmd5'],
            'newcontent': original['newcontent'],
        })
    return DiffRecord(**record_data)


def _confirm_diff(diff, status, comment, now):
    if diff.status == 0:
        return None

    original = _apply_confirm(diff, status, now)
    return _build_diff_record(original, _status_action(status), comment, now)


def _validate_confirm_form():
    comment = request.form.get('comment')
    status = request.form.get('status')
    if not comment or not _status_action(status):
        flash('输入无效.', 'error')
        return None, None
    return comment, status


@app.route('/diff/')
@app.route('/')
@login_required
def diff():
    hostname = request.args.get('hostname')
    type = request.args.get('type')
    page_size = _page_size()

    query = Diff.query
    if hostname:
        query = query.filter(Diff.hostname.like('{}%'.format(hostname)))
    if type:
        query = query.filter(Diff.type == type)

    if hostname or type:
        query = query.order_by(Diff.status.desc(), Diff.created_at.desc())
    else:
        query = query.order_by(Diff.status.desc(), Diff.updated_at.desc())

    page = int(request.args.get('page', 1))
    paginate = _pagination(query, page, page_size)
    pagination = Pagination(page=page, total=paginate.total, per_page=page_size, display_msg='展示 {start}-{end} , 总共 {total}')

    return render_template('diff.html', diffs=paginate.items, pagination=pagination, page='diff', hostname=hostname, type=type, page_size=page_size)


@app.route('/diff/show/<int:diff_id>')
@login_required
def diff_show(diff_id):
    diff = Diff.query.get_or_404(diff_id)
    return jsonify(diff.obj_to_dict())


@app.route('/diff/confirm/<int:diff_id>', methods=['POST'])
@login_required
def diff_confirm(diff_id):
    comment, status = _validate_confirm_form()
    if not comment:
        return redirect(request.referrer or url_for('diff'))

    diff = Diff.query.get_or_404(diff_id)
    record = _confirm_diff(diff, status, comment, datetime.now())
    if record is None:
        flash('已经是正常状态.', 'info')
        return redirect(request.referrer or url_for('diff'))

    db.session.add(record)
    db.session.commit()
    flash('标记成功.', 'success')
    return redirect(request.referrer or url_for('diff'))


@app.route('/diff/batchconfirm/', methods=['POST'])
@login_required
@admin_required
def diff_batch_confirm():
    checked = _selected_ids()
    if not checked:
        flash('未选中任何记录.', 'error')
        return redirect(request.referrer or url_for('diff'))

    comment, status = _validate_confirm_form()
    if not comment:
        return redirect(request.referrer or url_for('diff'))

    now = datetime.now()
    records = []
    for diff_id in checked:
        diff = Diff.query.get_or_404(diff_id)
        record = _confirm_diff(diff, status, comment + BATCH_COMMENT_SUFFIX, now)
        if record is not None:
            records.append(record)

    db.session.add_all(records)
    db.session.commit()
    flash('批量标记成功.', 'success')
    return redirect(request.referrer or url_for('diff'))


@app.route('/diff/delete/<int:diff_id>', methods=['POST'])
@login_required
@admin_required
def diff_delete(diff_id):
    diff = Diff.query.get_or_404(diff_id)
    db.session.delete(diff)
    db.session.commit()
    flash('删除成功.', 'success')
    return redirect(request.referrer or url_for('diff'))


@app.route('/diff/batchdelete', methods=['POST'])
@login_required
@admin_required
def diff_batch_delete():
    checked = _selected_ids()
    if not checked:
        flash('未选中任何记录.', 'error')
        return redirect(request.referrer or url_for('diff'))

    for diff_id in checked:
        db.session.delete(Diff.query.get_or_404(diff_id))
    db.session.commit()
    flash('批量删除成功.', 'success')
    return redirect(request.referrer or url_for('diff'))


@app.route('/diffrecord/')
@login_required
def diff_record():
    hostname = request.args.get('hostname')
    type = request.args.get('type')
    page_size = _page_size()

    query = DiffRecord.query
    if hostname:
        query = query.filter(DiffRecord.hostname.like('{}%'.format(hostname)))
    if type:
        query = query.filter(DiffRecord.type == type)
    query = query.order_by(DiffRecord.created_at.desc())

    page = int(request.args.get('page', 1))
    paginate = _pagination(query, page, page_size)
    pagination = Pagination(page=page, total=paginate.total, per_page=page_size, display_msg='展示 {start}-{end} , 总共 {total}')

    return render_template('diffrecord.html', diffs=paginate.items, pagination=pagination, page='diffrecord', hostname=hostname, type=type, page_size=page_size)


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
