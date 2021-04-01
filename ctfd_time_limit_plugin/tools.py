from sqlalchemy.sql.sqltypes import Time
from CTFd.models import db, Challenges, Solves
from .models import TimeLimit
from datetime import datetime, timedelta
from sqlalchemy import event
from sqlalchemy.orm import object_session
def create_if_not_exists_time_limit():
    chal_ids = [x.id for x in Challenges.query.filter(Challenges.id.notin_(TimeLimit.query.with_entities(TimeLimit.chalid)))]
    for id in chal_ids:
        tl = TimeLimit(id,datetime.now()+timedelta(days=30))
        db.session.add(tl)
    db.session.commit()

@event.listens_for(Challenges,'after_insert')
def listen_challenges_after_insert(mapper,connection,target):
    object_session(target).add(TimeLimit(chalid=target.id,timelimit=datetime.now()+timedelta(days=30)))


@event.listens_for(Solves,'after_insert')
def listen_sovles_after_insert(mapper,connection,target):
    pass
