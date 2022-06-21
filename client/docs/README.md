# SIPxTRTC WebApp Demo

## 说明

- > 腾讯实时音视频（Tencent Real-Time Communication，TRTC），将腾讯多年来在网络与音视频技术上的深度积累，以多人音视频通话和低延时互动直播两大场景化方案，通过腾讯云服务向开发者开放，致力于帮助开发者快速搭建低成本、低延时、高品质的音视频互动解决方案，([更多...](https://cloud.tencent.com/document/product/647/16788))
  >
  > TRTC SDK 支持 Web、Android、iOS、Windows以及Flutter、小程序等所有主流平台， ([更多平台...](https://github.com/LiteAVSDK?q=TRTC_&type=all&sort=)).

- > **[SIPx][] 实现互联网实时音视频和 [SIP][] 话路的互联互通。**
  >
  > 以多人音视频通话+电话互通，和低延时移动端通话+电话互通两大场景化方案，通过云服务向开发者开放， 致力于帮助开发者快速搭建低成本、低延时、高品质的移动音视频与VoIP话路互通解决方案。

## 功能

这个演示程序是一个简单的 WebApp，它在腾讯云官方演示程序 [TRTC Web 基础 Demo 在线体验](https://web.sdk.qcloud.com/trtc/webrtc/demo/latest/official-demo/index.html) 的基础上进行了修改。

通过这个 WebApp 进入 [TRTC][] 房间后，后台发起 [SIP][] 电话呼叫，将被叫手机拉入房间，进行语音对话。

## 支持哪些浏览器？

[TRTC][] Web SDK 对浏览器的详细支持度，您可以查看 [TRTC Web SDK 对浏览器支持情况](https://web.sdk.qcloud.com/trtc/webrtc/doc/zh-cn/tutorial-05-info-browser.html)。
对于上述没有列出的环境，您可以在当前浏览器打开 [TRTC 能力测试](https://web.sdk.qcloud.com/trtc/webrtc/demo/detect/index.html) 测试是否完整的支持 WebRTC 的功能。

## 开始体验

- 👉 [**点击这里**](https://demo.sipx.cn/release/trtc/web/) 开始体验

[sip]: https://datatracker.ietf.org/doc/html/rfc3261 "SIP: Session Initiation Protocol"
[sipx]: http://sipx.cn/ "实现互联网实时音视频和 SIP 话路的互联互通。"
[TRTC]: https://cloud.tencent.com/document/product/647/16788 "腾讯实时音视频（Tencent Real-Time Communication）"
