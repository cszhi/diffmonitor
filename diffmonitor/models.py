import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from diffmonitor import db
from datetime import datetime
import base64

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, index=True, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Diff(db.Model):
    #__tablename__ = 'diff'
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(32), nullable=False, index=True, comment='主机名称') #unique=True
    ip = db.Column(db.String(32), comment='主机管理IP')
    type = db.Column(db.String(32), nullable=False, index=True, comment='监控类型')
    md5 = db.Column(db.String(32), nullable=False)
    newmd5 = db.Column(db.String(32))
    content = db.Column(db.Text)
    newcontent = db.Column(db.Text)
    diff = db.Column(db.Text)
    status = db.Column(db.Integer, server_default='0')
    created_at = db.Column(db.DateTime, index=True, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    comment = db.Column(db.Text)

    #https://blog.csdn.net/u011089760/article/details/90142672
    def obj_to_dict(self):
        return {
            "id":self.id,
            "hostname":self.hostname,
            "ip":self.ip,
            "type":self.type,
            "md5":self.md5,
            "newmd5":self.newmd5,
            "content":self.content if self.content else '-',
            "newcontent":self.newcontent if self.newcontent else '-',
            "diff":self.diff if self.diff else '-',
            "status":self.status,
            "created_at":self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at":self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "comment":self.comment if self.comment else '-'
        }
    def obj_to_dict2(self):
        return {
            "hostname":self.hostname,
            "type":self.type
        }


class DiffRecord(db.Model):
    #__tablename__ = 'diffrecords'
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(32), nullable=False, index=True)
    ip = db.Column(db.String(32))
    type = db.Column(db.String(32), nullable=False, index=True)
    md5 = db.Column(db.String(32), nullable=False)
    newmd5 = db.Column(db.String(32))
    content = db.Column(db.Text)
    newcontent = db.Column(db.Text)
    diff = db.Column(db.Text)
    status = db.Column(db.Integer, server_default='0')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    username = db.Column(db.String(32), comment='操作人员')
    action = db.Column(db.String(32))
    comment = db.Column(db.Text)

    def obj_to_dict(self):
        return {
            "id":self.id,
            "hostname":self.hostname,
            "ip":self.ip,
            "type":self.type,
            "md5":self.md5,
            "newmd5":self.newmd5,
            "content":self.content if self.content else '-',
            "newcontent":self.newcontent if self.newcontent else '-',
            "diff":self.diff if self.diff else '-',
            "status":self.status,
            "created_at":self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "username":self.username if self.username else '-',
            "action":self.action if self.action else '-',
            "comment":self.comment if self.comment else '-'
        }
