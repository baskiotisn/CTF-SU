from flask import jsonify, request, Blueprint, session, render_template,redirect,url_for
from CTFd.models import db, Challenges
from CTFd.utils.decorators import admins_only
from CTFd.utils.helpers import get_infos,markup
from .models import TimeLimit
import dateutil.parser

plugin_blueprint = Blueprint(
    "time_limit", __name__, template_folder="assets")


@plugin_blueprint.route("/admin/time_limit", methods=["GET","POST"])
@admins_only
def time_limit():
    challenges = [{"chalid":c.id, "name":c.name, "timelimit":t.timelimit} for c,t in db.session.query(Challenges,TimeLimit).filter(Challenges.id==TimeLimit.chalid)]
    return render_template("time_limit.html", challenges=challenges)


@plugin_blueprint.route("/admin/time_limit/<int:chal_id>/update", methods=["POST"])
@admins_only
def update_timelimit(chal_id):
    chal = Challenges.query.filter_by(id=chal_id).first_or_404()
    timelimit = request.form.get("update_timelimit")

    # convert string of the form 2018-06-12T19:30 to a datetime
    timelimit = dateutil.parser.parse(timelimit)

    tr = db.session.query(TimeLimit).filter(
        TimeLimit.chalid == chal_id).first()
    if tr is None:
        db.session.add(TimeLimit(chalid=chal_id, timelimit=timelimit))
    else:
        # if it already existed then update it
        tr.timelimit = timelimit
    db.session.commit()
    db.session.close()
    return redirect("/admin/time_limit")

