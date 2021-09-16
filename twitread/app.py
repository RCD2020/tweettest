"""My web application for pulling twitter users and tweets.

Robert Davis
2021/09/14"""


from sklearn.linear_model import LogisticRegression
from flask import Flask, render_template, request
from .models import db, User, Tweet
import en_core_web_sm
import numpy as np
import tweepy
import spacy
import os


app_dir = os.path.dirname(os.path.abspath(__file__))
database = f'sqlite:///{os.path.join(app_dir, "twitter.sqlite3")}'
nlp_model = spacy.load('my_nlp_model')


def retrieve_keys(
    path='/Users/colby/Documents/Lambda/03 Unit 3/twitterapi.keys'
):
    """Retrieves my twitter api keys because .env files won't work"""

    file = open(
        '/Users/colby/Documents/Lambda/03 Unit 3/twitterapi.keys',
        'r'
    )

    data = file.read().split('\n')

    keys = {}

    for x in data:
        y = x.split('=')

        keys[y[0]] = y[1]

    return keys


def twit_connect(keys=retrieve_keys()):
    """Connects to twitter. Returns a tweepy.API object."""

    auth = tweepy.OAuthHandler(keys['KEY'], keys['SECRET'])
    twitter = tweepy.API(auth)

    return twitter


def model_users(user1, user2, text):
    """Input the two users and the tweet you are predicting.
    Outputs good the goods.\n
    ```json
    {
        "winner": <prediction results>,
        "user1": {
            "name": <user 1 display name>,
            "tweetAmount": <user 1 tweet amount>
        },
        "user2": {
            "name": <user 2 display name>,
            "tweetAmount": <user 2 tweet amount>
        },
        "text": <text>
    }
    ```"""

    tweets1 = user1.timeline(count=200, exclude_replies=True,
        include_rts=False, tweet_mode='Extended')
    tweets2 = user2.timeline(count=200, exclude_replies=True,
        include_rts=False, tweet_mode='Extended')

    vecify = lambda text : nlp_model(text).vector
    vec1 = np.array([vecify(tweet.text) for tweet in tweets1])
    vec2 = np.array([vecify(tweet.text) for tweet in tweets2])
    vects = np.vstack([vec1, vec2])

    len1, len2 = len(vec1), len(vec2)

    labels = np.concatenate([np.zeros(len1), np.ones(len2)])

    logreg = LogisticRegression().fit(vects, labels)

    prediction = logreg.predict(vecify(text).reshape(1, -1))[0]

    if prediction == 0:
        winner = user1.screen_name
    else:
        winner = user2.screen_name

    info = {
        'winner': winner,
        'user1': {
            'name': user1.screen_name,
            'tweetAmount': len1
        },
        'user2': {
            'name': user2.screen_name,
            'tweetAmount': len2
        },
        'text': text
    }

    return info


def create_app():
    """Creates the application"""

    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = database
    app.config['SQLALCHEMY_TRACK_NOTIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    twitter = twit_connect()


    @app.route('/')
    def indexPage():
        return render_template('index.html')

    @app.route('/users', methods=['GET', 'POST'])
    def usersPage():
        name = request.form.get('name')
        message = ['' for x in range(1)]
        users = User.query.all()

        if name:
            try:
                twituser = twitter.get_user(name)

                user = User(name=name)
                tweets = twituser.timeline(
                    count=3, exclude_replies=True,
                    include_rts=False, tweet_mode='Extended'
                )

                for tweet in tweets:
                    tweetObj = Tweet(userid=users[-1].id+1,
                        text=tweet.text)
                    db.session.add(tweetObj)

                db.session.add(user)
                message[0] = f'Added user @{name} successfully'
                db.session.commit()
            except:
                message[0] = f'Could not find user @{name}'

        users = User.query.all()
        return render_template(
            'users.html', users=users,
            message=message)

    @app.route('/tweets', methods=['GET', 'POST'])
    def tweetsPage():
        users = User.query.all()
        tweets = Tweet.query.all()
        vector = request.form.get('vector')

        if vector:
            vectored = nlp_model(tweets[int(vector)-1].text).vector
        else:
            vectored = 'Vector will appear here.'

        return render_template('tweets.html',
            users=users, tweets=tweets, vector=vectored)

    # @app.route('/iris')
    # def iris():
    #     from sklearn.datasets import load_iris
    #     from sklearn.linear_model import LogisticRegression

    #     X, y = load_iris(return_X_y=True)
    #     clf = LogisticRegression(
    #         random_state=0,
    #         solver='lbfgs',
    #         multi_class='multinomial'
    #     ).fit(X, y)

    #     return str(clf.predict(X[:2, :]))

    @app.route('/model', methods=['GET', 'POST'])
    def modelPage():
        name1 = request.form.get('name1')
        name2 = request.form.get('name2')
        testtweet = request.form.get('tweet')
        modelOutput = 'This is where the results are displayed.'

        if testtweet:
            results = [0, 0]
            modelOutput = ''
            try:
                user1 = twitter.get_user(name1)

                if len(user1.timeline(
                    count=1, exclude_replies=True,
                    include_rts=False, tweet_mode='Extended')) > 0:
                    results[0] = 1
                else:
                    modelOutput += f"Can't find tweets from @{name1}. "
            except:
                modelOutput += f'@{name1} is an invalid username. '

            try:
                user2 = twitter.get_user(name2)
                if len(user1.timeline(
                    count=1, exclude_replies=True,
                    include_rts=False, tweet_mode='Extended')) > 0:
                    results[1] = 1
                else:
                    modelOutput += f"Can't find tweets from @{name2}."
            except:
                modelOutput += f'@{name2} invalid username.'

            if results == [1, 1]:
                info = model_users(user1, user2, testtweet)

                modelOutput = f"Using @{name1}'s \
{info['user1']['tweetAmount']} tweets and @{name2}'s \
{info['user2']['tweetAmount']} tweets, I conclude that '{info['text']}' \
sounds like something @{info['winner']} would say.'"

        return render_template('model.html', modelOutput=modelOutput)

    return app
