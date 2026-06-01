import os
import secrets

import click

from diffmonitor import app, db
from diffmonitor.models import User, Diff, DiffRecord

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()

    username = 'admin'
    user = User.query.filter(User.username == username).first()
    if user is not None:
        click.echo('Admin user already exists. Skip creating default admin.')
        click.echo('Initialized database.')
        return

    password = os.getenv('ADMIN_PASSWORD')
    if not password:
        password = secrets.token_urlsafe(16)
        click.echo('ADMIN_PASSWORD is not set. Generated admin password: {}'.format(password))

    user = User(username=username, is_admin=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo('Created admin user: {}'.format(username))
    click.echo('Initialized database.')

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.filter(User.username == username ).first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, is_admin=False)
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')
