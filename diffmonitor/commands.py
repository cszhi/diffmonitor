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
    user = User(
        username=username, 
        is_admin=True, 
        password_hash='pbkdf2:sha256:260000$lpIPQMSnBRpdSSSf$dd059672c41336d39fbaf0a02c168ecd50d18fe824b40c55059102d4dbcd252c' #Admin123
    )
    db.session.add(user)
    db.session.commit()

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