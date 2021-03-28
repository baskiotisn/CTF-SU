#from CTFd.plugins import register_plugin_assets_directory
#from models import 
#from routes import plugin_blueprint, get_available_challenges
#from utils import satisfies_challenge_dependencies, satisfies_hint_dependencies
from CTFd.plugins import register_plugin_assets_directory
from .routes import plugin_blueprint
from .tools import create_if_not_exists_time_limit
def load(app):
#    def wrap_method(name, wrapper):
#        old = app.view_functions[name]
#        app.view_functions[name] = wrapper(old)

    app.db.create_all()

    app.register_blueprint(plugin_blueprint)
    register_plugin_assets_directory(app, base_path="/plugins/ctfd-time_limit-plugin/assets/")
    create_if_not_exists_time_limit()