import logging.config
from os import getenv
from urllib.parse import urljoin

from flask import Flask, redirect, url_for
from werkzeug import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.routing import BaseConverter


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super().__init__(url_map)
        self.regex = items[0]


app = Flask(__name__)
app.url_map.converters['regex'] = RegexConverter  # type: ignore


cfg_env = app.config['ENV']
if cfg_env == 'production':
    cfg_pyfile = 'config.py'
else:
    cfg_pyfile = f'config.{cfg_env}.py'
app.config.from_pyfile(cfg_pyfile)

logging.config.dictConfig(app.config['LOGGING_CONFIG'])


for name in ('static_folder', 'template_folder', ):
    value = app.config.get('APP_' + name.upper())
    if value:
        setattr(app, name, value)


if app.config.get('CORS_ENABLED'):
    from flask_cors import CORS
    CORS(app)


# 自定义用于模板中的 static 过滤函数，计算 static 地址
@app.template_filter(name='static')
def static_filter(filename):
    static_base_url = app.config.get('APP_STATIC_BASE_URL')
    if static_base_url:
        return urljoin(static_base_url, filename)
    # 如果没设置，按照默认 static 处理
    return url_for('static', filename=filename)


# 动态请求不再模板中，无法提前计算 static 地址，用这个 viewer 进行 redirect
@app.route('/<regex("(js|img|css|data)/(.+)"):filename>')
def static_view(filename):
    static_base_url = app.config.get('APP_STATIC_BASE_URL')
    if static_base_url:
        return redirect(urljoin(static_base_url, filename))
    return app.send_static_file(filename)


with app.app_context():
    import views as _


if __name__ == '__main__':
    # First: set the time conversion rules used by the library routines.
    # The environment variable TZ specifies how this is done.
    try:
        from time import tzset  # type: ignore
    except ImportError:
        pass  # Availability only on Unix.
    else:
        tzset()
    # 用于兼容腾讯云 SCF HTTP 直通函数,
    # 由于它是基于 docker 镜像运行，所以必须监听地址为 0.0.0.0，并且端口为 9000
    # 为了适应 云服务 API GateWay 的路径前缀, 使用 Application Dispatching.
    # 参考: https://flask.palletsprojects.com/patterns/appdispatch/
    if getenv('TENCENTCLOUD_RUNENV') == 'SCF':
        application_root = app.config.get('APPLICATION_ROOT')
        if application_root:
            wsgi_app = DispatcherMiddleware(
                Flask(__name__),
                {application_root: app}
            )
        else:
            wsgi_app = app
        # 用于兼容腾讯云 SCF HTTP 直通函数,
        # 由于它是基于 docker 镜像运行，所以必须监听地址为 0.0.0.0，并且端口为 9000
        run_simple('', 9000, wsgi_app)
    else:
        app.run()
