import urllib.parse
from hashlib import blake2b
from logging import getLogger
from random import choices, randint
from time import time

import phonenumbers
import requests
from flask import (abort, current_app, jsonify, render_template, request,
                   session)
from TLSSigAPIv2 import TLSSigAPIv2

from utils import (dismiss_trtc_room, make_sipx_signature,
                   send_sms_validity_code)

SMS_VALIDATE_SEND_TIMEOUT = 45
SMS_VALIDATE_LIVE_TIMEOUT = 600


@current_app.route('/hello')
def hello():
    return 'Hello! It worked!'


@current_app.route('/')
def index():
    return render_template('index.html')


@current_app.route('/sms_code', methods=['POST'])
def sms_code():
    logger = getLogger(__name__)
    timestamp = session.get('timestamp')
    if timestamp and time() - timestamp < SMS_VALIDATE_SEND_TIMEOUT:
        return f'{SMS_VALIDATE_SEND_TIMEOUT} 秒之内不要重复提交短信验证请求！', 403
    req = request.get_json(force=True)
    if not req:
        return '无效的请求参数', 400
    try:
        pn_obj = phonenumbers.parse(req['phoneNumber'], 'CN')
    except KeyError:
        return '无效的会话数据', 400
    except phonenumbers.NumberParseException:
        return '无效的电话号码', 400
    else:
        if not phonenumbers.is_valid_number_for_region(pn_obj, 'CN'):
            return '无效的电话号码', 400
    phone_number = phonenumbers.format_number(
        pn_obj, phonenumbers.PhoneNumberFormat.E164)
    if not phone_number.startswith('+861'):
        return '不是手机号码', 400

    # 计算验证码，6位数字的
    validity_code = ''
    if current_app.config['ENV'] != 'production':
        validity_code = current_app.config.get(
            'APP_DEVELOPMENT_SMS_VALIDITY_CODE')
        logger.debug('APP_DEVELOPMENT_SMS_VALIDITY_CODE: %s - %s',
                     phone_number, validity_code)
    if not validity_code:
        validity_code = ''.join(str(n) for n in choices(range(10), k=6))
        send_sms_validity_code(phone_number, validity_code)
        logger.info('已发送验证短信码 SMS Validation Code: %s - %s',
                    phone_number, validity_code)

    # 在 Cookie 中加密保存验证码、手机号信息，未来验证用
    session['phone_number'] = phone_number
    session['validity_code'] = validity_code
    session['timestamp'] = time()

    # 返回验证码再次请求的超时时间
    return jsonify({
        'sendTimeout': SMS_VALIDATE_SEND_TIMEOUT,
        'liveTimeout': SMS_VALIDATE_LIVE_TIMEOUT,
    })


@current_app.route('/enter_room', methods=['POST'])
def enter_room():
    """进房

    不是真的进房（这要客户端自己完成），这里只是把进房的参数传过去
    """
    logger = getLogger(__name__)
    req = request.get_json(force=True)
    if not req:
        return abort(400)
    try:
        validity_code = req['smsCode']
    except KeyError:
        return '未提供或错误的验证码，无法进入 TRTC 房间', 400
    try:
        timestamp = session['timestamp']
        saved_validity_code = session['validity_code']
    except KeyError:
        return '未提供或错误的验证码，无法进入 TRTC 房间。\r\n提示: 该程序需要允许 Cookie 方可正常运行。', 400
    if time() - timestamp > SMS_VALIDATE_LIVE_TIMEOUT:
        return '验证码已过期', 403
    if validity_code != saved_validity_code:
        return '验证码错误', 403

    # 随机一个TRTC用户ID并签名；随机一个roomID。注意并发时不要重复！
    # FIXME:  RoomID/UserID 有重复的风险
    room_id = None
    if current_app.config['ENV'] == 'development':
        room_id = current_app.config.get('APP_DEVELOPMENT_TRTC_ROOM_ID')
    if not room_id:
        room_id = randint(2147483648, 4294967294)
    user_id = blake2b(f'{room_id}'.encode('ascii'), digest_size=4).hexdigest()
    trtc_sig = TLSSigAPIv2(
        current_app.config['TENCENTCLOUD_TRTC_SDK_APP_ID'],
        current_app.config['TENCENTCLOUD_TRTC_SECRET_KEY'],
    )
    user_sig = trtc_sig.gen_sig(user_id, expire=600)
    # 进房参数同时也是 Session 标记：验证码 OK
    trtc_params = session['trtc_params'] = {
        'sdkAppId': current_app.config['TENCENTCLOUD_TRTC_SDK_APP_ID'],
        'userId': user_id,
        'userSig': user_sig,
        'roomId': room_id,
    }
    logger.info('进房参数: %s', trtc_params)
    return jsonify(trtc_params)


@current_app.route('/make_call', methods=['POST'])
def make_call():
    """进房后，开始拨号呼叫
    """
    logger = getLogger(__name__)
    try:
        timestamp = session['timestamp']
        phone_number = session['phone_number']
        room_id = session['trtc_params']['roomId']
    except KeyError:
        return '未提供或错误的验证码，无法进入 TRTC 房间。\r\n提示: 该程序需要允许 Cookie 方可正常运行。', 400
    if time() - timestamp > SMS_VALIDATE_LIVE_TIMEOUT:
        return '验证码已过期', 403

    pn_obj = phonenumbers.parse(phone_number)
    national_phone_number = ''.join(
        phonenumbers
        .format_number(pn_obj, phonenumbers.PhoneNumberFormat.NATIONAL)
        .split()
    )
    # TRTC 签名
    # 注意要同一个 房间，不同用户！
    # 不要和给 web 用户的  trtcParams  混淆！
    user_id = f'tel_{national_phone_number}'
    trtc_sig = TLSSigAPIv2(
        current_app.config['TENCENTCLOUD_TRTC_SDK_APP_ID'],
        current_app.config['TENCENTCLOUD_TRTC_SECRET_KEY'],
    )
    user_sig = trtc_sig.gen_sig(user_id, expire=600)

    # 调用 SIPX 的 API
    sipx_auth_params = {
        'api_key': current_app.config['SIPX_OPENAPI_KEY'],
        'expire_at': int(time()) + 600,
    }
    sipx_auth_params['signature'] = make_sipx_signature(
        sipx_auth_params['api_key'],
        current_app.config['SIPX_OPENAPI_SECRET'],
        sipx_auth_params['expire_at']
    )

    body = {
        'trtcParams': {
            'sdkAppId': current_app.config['TENCENTCLOUD_TRTC_SDK_APP_ID'],
            "userId": user_id,
            "userSig": user_sig,
            "roomId": room_id
        },
        'phonenumber': national_phone_number,
    }

    public_url = current_app.config.get('APP_SERVER_PUBLIC_URL')
    if public_url:
        body.update({
            # call-state web callback: room id 用于配对！
            'callStateNotifyUrl': '{APP_SERVER_PUBLIC_URL}/call_state_notify?{0}'.format(
                urllib.parse.urlencode({
                    'room_id': str(room_id),
                    'phone_number': phone_number,
                }),
                **current_app.config
            )})

    logger.info('开始呼叫 %s 进房 %s', phone_number, room_id)
    r = requests.post(
        '{}/trtc/startup'.format(current_app.config['SIPX_OPENAPI_URL']),
        params=sipx_auth_params,
        json=body,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as err:
        if r.status_code in range(400, 500):
            err_data = r.json()
            logger.error('%s:\n\t%s', err, err_data)
            return err_data.get('message'), 500
        else:
            raise
    else:
        d = r.json()
        logger.info('呼叫启动成功: %s: %s <=> %s', d['id'], room_id, phone_number)

    # 呼叫成功后清空 session! （只需要删除 timestamp, validity_code）
    del session['timestamp']
    del session['validity_code']
    return b''


@ current_app.route('/exit_room', methods=['POST'])
def exit_room():
    """出房

    不是真的出房（这要客户端自己完成），这里只是客户端退出后，通知服务器
    """
    try:
        trtc_params = session['trtc_params']
        room_id = trtc_params['roomId']
    except KeyError:
        return '会话数据格式错误。\r\n提示: 该程序需要允许 Cookie 方可正常运行。', 400
    logger = getLogger(__name__)
    logger.info('Room(%s) RTC 一侧用户已退出', room_id)
    dismiss_trtc_room(room_id, ignore_codes=['FailedOperation.RoomNotExist'])
    return b''


@ current_app.route('/call_state_notify', methods=['POST'])
def call_state_notify():
    logger = getLogger(__name__)
    room_id = int(request.args['room_id'])
    phone_number = request.args['phone_number']
    data = request.get_json(force=True)
    logger.info('call_state_notify: (%s %s) %s', room_id, phone_number, data)
    if data['state_text'] == 'DISCONNCTD':  # type: ignore
        dismiss_trtc_room(room_id, ignore_codes=[
                          'FailedOperation.RoomNotExist'])
    return b''
