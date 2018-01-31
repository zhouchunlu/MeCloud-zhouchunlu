# coding=utf8

import tornado.web

from util.WxPaySDK import Wxpay_server_pub
from wsserver import logger


# 微信支付回调
class WxCallbackHandler(tornado.web.RequestHandler):
    def get(self, action=None):
        pass

    def post(self):
        xml = self.request.body
        logger.debug('xml: %s', xml)
        pub = Wxpay_server_pub()
        pub.saveData(xml)
        logger.debug('pub.data: %s', pub.data)
        if pub.data['return_code'] == 'SUCCESS' and pub.data['result_code'] == 'SUCCESS':
            print 'wx call back result is success'
        # TODO update order status and notify cilent with websocket
        self.write('<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>')
