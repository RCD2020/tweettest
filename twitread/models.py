"""Classes for TwitterAPI project.

Robert Davis
2021/09/14"""


from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    """The User class is used to store twitter users."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tweets = db.relationship('Tweet', backref='user', lazy=True)

    def __repr__(self):
        return f'<User Object: {self.name}>'

class Tweet(db.Model):
    """The Tweet class us used to store tweets from twitter."""

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Tweet Object: {self.id}>'
