################
# Flask config #
################
# Flask Session's cookie secret key
# SECRET_KEY = 'xxxx'
# 实际部署时，由于各种服务/代理/网关等的前缀地址，可能需要设置这几个 FLASK 参数
# APPLICATION_ROOT = '/trtc/web'
# SESSION_COOKIE_PATH = '/release/trtc/web'

#####################
# Flask-CORS config #
#####################
# 如果需要 CORS，将它设为 True
# 其它设置参考 https://flask-cors.readthedocs.io/
# CORS_ENABLED = False

########################
# TencentCloud API Key #
########################
TENCENTCLOUD_SECRET_ID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TENCENTCLOUD_SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TENCENTCLOUD_TRTC_SDK_APP_ID = 8888888888
TENCENTCLOUD_TRTC_SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
TENCENTCLOUD_SMS_SDK_APP_ID = 8888888888
TENCENTCLOUD_SMS_SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TENCENTCLOUD_SMS_SIGN_NAME = 'xxxxxx'
TENCENTCLOUD_SMS_TEMPLATE_ID = 888888

######################
# Application config #
######################
# 开发期间，可以直接用 client 作为模板目录
APP_TEMPLATE_FOLDER = '../client'
# 开发期间，可以直接用 client 作为 static 目录路径
APP_STATIC_FOLDER = '../client'
# 部署后，可以用静态的 URL 作为 static 路径
# APP_STATIC_BASE_URL = 'http://localhost:8082/'

# Web 服务的公网 Base URL
# APP_SERVER_PUBLIC_URL = 'http://localhost:8081'

# 假的短信验证码，用于开发调试
APP_DEVELOPMENT_SMS_VALIDITY_CODE = '000000'
# 固定的房间，方便开发调试
# APP_DEVELOPMENT_TRTC_ROOM_ID = 1001

##########################
# SIPX WebService config #
##########################
# SIPx 的地址和 API key/secret
# 换成你的
SIPX_OPENAPI_URL = 'http://api.sipx.cn/v2205'
SIPX_OPENAPI_KEY = '88888888'
SIPX_OPENAPI_SECRET = 'xxxxxxxx'

##################
# Logging config #
##################
LOGGING_CONFIG = {
    'version': 1,
    'root': {
        'level': 'DEBUG',
        'handlers': ['stderr'],
    },
    'handlers': {
        'stderr': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'default',
        },
    },
    'formatters': {
        'default': {
            'format': '%(levelname)-7s %(asctime)s %(process)d [%(name)s]\t%(message)s',
        }
    },
    'loggers': {
        'urllib3': {
            'level': 'INFO',
        },
        'tencentcloud_sdk_common': {
            'level': 'INFO',
        },
    }
}
