# coding=utf8
import urllib

import tornado

from util.alipay_core import *


class AlipayCallbackHandler(tornado.web.RequestHandler):
    def get(self, action=None):
        pass

    def post(self):
        args = self.request.arguments
        for k, v in args.items():
            args[k] = v[0]

        check_sign = params_to_query(args)
        params = query_to_dict(check_sign)
        sign = params['sign']
        toSignDict = {}
        for k, v in params.items():
            if k == 'sign' or k == 'sign_type':
                continue
            str = urllib.parse.unquote_plus(v)
            toSignDict[k] = str
        # params = params_filter(params)
        message = params_to_query(params, quotes=False, reverse=False)  # 获取到要验证签名的串
        check_res = check_ali_sign(message, sign)  # 验签

        if check_res == False:
            self.write("fail")
            return

        # 这里是去访问支付宝来验证订单是否正常
        # res = verify_from_gateway({"partner": alipay_config.partner_id, "notify_id": params["notify_id"]})
        # if res == False:
        #     self.write("fail")
        #     return

        trade_status = params["trade_status"]
        order_id = params["out_trade_no"]  # 你自己构建订单时候的订单ID
        alipay_order = params["trade_no"]  # 支付宝的订单号码
        total_fee = params["total_amount"]  # 支付总额

        """
        下面是处理付款完成的逻辑
        """
        if trade_status == "TRADE_SUCCESS":  # 交易成功
            # TODO:订单付款后的操作
            self.write("success")
            return
        if trade_status == "TRADE_FINISHED":
            return

        if trade_status == "WAIT_BUYER_PAY":
            self.write("success")
            return
        if trade_status == "TRADE_CLOSED":  # 退款会回调这里
            self.write("success")
