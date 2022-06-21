import hmac
import json
from base64 import urlsafe_b64encode
from logging import getLogger

from flask import abort, current_app, make_response
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import \
    TencentCloudSDKException
from tencentcloud.sms.v20210111 import models as sms_models
from tencentcloud.sms.v20210111 import sms_client
from tencentcloud.trtc.v20190722 import models as trtc_models
from tencentcloud.trtc.v20190722 import trtc_client


def make_sipx_signature(api_key: str, api_key_secret: str, expire_at: int) -> str:
    x = hmac.new(api_key_secret.encode('ascii'), digestmod='sha256')
    x.update(api_key.encode('ascii'))
    x.update(str(int(expire_at)).encode('ascii'))
    digested = x.digest()
    s = urlsafe_b64encode(digested).decode('ascii').rstrip('=')
    return s


def dismiss_trtc_room(room_id, ignore_codes=None):
    logger = getLogger('dismiss_trtc_room')
    params = {
        'SdkAppId': current_app.config['TENCENTCLOUD_TRTC_SDK_APP_ID'],
        'RoomId': room_id,
    }
    try:
        cred = credential.Credential(
            current_app.config['TENCENTCLOUD_SECRET_ID'], current_app.config['TENCENTCLOUD_SECRET_KEY'])
        client = trtc_client.TrtcClient(cred, 'ap-guangzhou')
        req = trtc_models.DismissRoomRequest()
        logger.debug('解散 TRTC 房间 (%s)', params)
        req.from_json_string(json.dumps(params))
        client.DismissRoom(req)
    except TencentCloudSDKException as err:
        if ignore_codes and err.code in ignore_codes:
            # 不用管的错误
            logger.debug(
                '被忽略的 TencentCloudSDKException : 解散 TRTC 房间 (%s) 失败: %s', params, err)
        else:
            logger.warning('解散 TRTC 房间 (%s) 失败: %s', params, err)
            abort(make_response(
                f'TRTC DismissRoomRequest 失败 ({err.code}): {err.message}',
                500
            ))


def send_sms_validity_code(phone_number: str, code: str):
    """通过腾讯云发送短信

    see: https://cloud.tencent.com/document/product/382/43196
    """
    logger = getLogger('send_sms_validity_code')
    params = {
        # 应用 ID 可前往 [短信控制台](https://console.cloud.tencent.com/smsv2/app-manage) 查看
        'SmsSdkAppId': str(current_app.config['TENCENTCLOUD_SMS_SDK_APP_ID']),
        # 短信签名内容: 使用 UTF-8 编码，必须填写已审核通过的签名
        'SignName': current_app.config['TENCENTCLOUD_SMS_SIGN_NAME'],
        # 模板 ID 可前往 [国内短信](https://console.cloud.tencent.com/smsv2/csms-template) 或 [国际/港澳台短信](https://console.cloud.tencent.com/smsv2/isms-template) 的正文模板管理查看
        'TemplateId': str(current_app.config['TENCENTCLOUD_SMS_TEMPLATE_ID']),
        # 模板参数: 模板参数的个数需要与 TemplateId 对应模板的变量个数保持一致，，若无模板参数，则设置为空
        'TemplateParamSet': [code],
        # 下发手机号码，采用 E.164 标准，+[国家或地区码][手机号]
        'PhoneNumberSet': [phone_number],
        # 用户的 session 内容（无需要可忽略）: 可以携带用户侧 ID 等上下文信息，server 会原样返回
        # 'SessionContext': '',
        # 短信码号扩展号（无需要可忽略）: 默认未开通，如需开通请联系 [腾讯云短信小助手]
        # 'ExtendCode': '',
        # 国际/港澳台短信 senderid（无需要可忽略）: 国内短信填空，默认未开通，如需开通请联系 [腾讯云短信小助手]
        # 'SenderId': '',
    }
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户密钥对secretId，secretKey。
        cred = credential.Credential(
            current_app.config['TENCENTCLOUD_SECRET_ID'], current_app.config['TENCENTCLOUD_SECRET_KEY'])
        # 实例化要请求产品(以sms为例)的client对象
        # 第二个参数是地域信息，可以直接填写字符串ap-guangzhou，支持的地域列表参考 https://cloud.tencent.com/document/api/382/52071#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
        client = sms_client.SmsClient(cred, 'ap-guangzhou')
        # 实例化一个请求对象，根据调用的接口和实际情况，可以进一步设置请求参数
        req = sms_models.SendSmsRequest()
        req.from_json_string(json.dumps(params))
        # 发送！
        logger.debug('发送短信验证码 (%s)', phone_number)
        res: sms_models.SendSmsResponse = client.SendSms(req)

    except TencentCloudSDKException as err:
        logger.warning('发送短信验证码 (%s) 失败: %s', phone_number, err)
        abort(make_response(
            f'SendSms 失败 ({err.code}): {err.message}',
            500
        ))
    else:
        assert res.SendStatusSet is not None
        st: sms_models.SendStatus = res.SendStatusSet[0]
        if st.Code != 'Ok':
            logger.warning('发送短信验证码 (%s) 失败: %s', phone_number, st)
            abort(make_response(
                f'SendSms 失败 ({st.Code}): {st.Message}',
                500
            ))
