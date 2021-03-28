from CTFd.models import db
from datetime import datetime

class TimeLimit(db.Model):
    chalid = db.Column(db.Integer, db.ForeignKey('challenges.id'),primary_key=True)
    timelimit = db.Column(db.DateTime)

    def __init__(self, chalid, timelimit):
        self.chalid = chalid
        self.timelimit = timelimit

    def __repr__(self):
        return '<limit {}, {}>'.format(self.chalid, self.timelimit)
    @property
    def ended(self):
        return self.timelimit<datetime.now()

"""
@cache.memoize()
def get_score(self, admin=False):
    score = db.func.sum(Challenges.value).label("score")
    user = (
         db.session.query(Solves.user_id, score)
         .join(Users, Solves.user_id == Users.id)
         .join(Challenges, Solves.challenge_id == Challenges.id)
         .filter(Users.id == self.id)
         )

     award_score = db.func.sum(Awards.value).label("award_score")
      award = db.session.query(award_score).filter_by(user_id=self.id)

       if not admin:
            freeze = Configs.query.filter_by(key="freeze").first()
            if freeze and freeze.value:
                freeze = int(freeze.value)
                freeze = datetime.datetime.utcfromtimestamp(freeze)
                user = user.filter(Solves.date < freeze)
                award = award.filter(Awards.date < freeze)

        user = user.group_by(Solves.user_id).first()
        award = award.first()

        if user and award:
            return int(user.score or 0) + int(award.award_score or 0)
        elif user:
            return int(user.score or 0)
        elif award:
            return int(award.award_score or 0)
        else:
            return 0
"""