# coding=utf8
import traceback
import json

import tornado.web
from mecloud.api.BaseHandler import BaseHandler, MeQuery, MeObject
from mecloud.lib import PayUtil

from util import alipay_config, alipay_core
from util.ErrorInfo import *
from util.WxPaySDK import UnifiedOrder_pub, WxPayConf_pub
from wsserver import logger
from util.payUtil import orderCallback

from mecloud.helper.ClassHelper import ClassHelper
from mecloud.helper.Util import MeEncoder, createOrderNo
from mecloud.lib import log
from mecloud.model.MeError import *
import datetime


class PayHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, action=None):
        pass

    @tornado.web.authenticated
    def post(self, action=None):
        try:
            if action == 'createWxAppOrder':
                self.createWxAppOrder()
            elif action == 'createAppleOrder':
                self.recharge()
            elif action == 'applePayComplete':
                self.payComplete()
            elif action == 'createAlipayAppOrder':
                self.createAlipayAppOrder()
            else:
                print "action error: " + action
        except Exception, e:
            logger.error(e)
            msg = traceback.format_exc()
            logger.error(msg)
            self.write(ERR_PARA.message)

    # 微信APP支付下单
    def createWxAppOrder(self):
        logger.debug(self.jsonBody)
        obj = self.jsonBody
        coin_setting_id = obj.get('id')  # coinSettingId
        channel = obj.get('channel', '')
        version = obj.get('version', '')
        logger.debug('coin_setting_id: %s', coin_setting_id)
        coin_setting = MeObject('CoinSetting').get(coin_setting_id)
        logger.debug('coin_setting: %s', coin_setting)
        if coin_setting is None:
            # 未找到充值条目
            self.write(ERR_PAY_NOT_FIND_COIN_SETTING.message)
            return
        out_trade_no = PayUtil.createOrderNo()
        logger.debug('out_trade_no: %s', out_trade_no)
        pub = UnifiedOrder_pub()
        pub.parameters['out_trade_no'] = out_trade_no  # 设置参数自己的订单号
        pub.parameters['body'] = '黑密虚拟商品-黑密滴' + str(coin_setting['amount']) + '个'  # 设置商品描述
        pub.parameters['total_fee'] = str(coin_setting['price'])  # 设置总金额
        pub.parameters['notify_url'] = WxPayConf_pub.NOTIFY_URL  # 设置回调url
        pub.parameters['trade_type'] = 'APP'  # 支付类型，固定为app
        wx_result = pub.getResult()
        logger.info('wx create order result: %s', wx_result)

        if wx_result['return_code'] == 'SUCCESS':
            logger.debug('prepay_id: %s', wx_result['prepay_id'])
            result = {}
            result['code'] = 0
            result['prepayid'] = wx_result['prepay_id']
            result['appid'] = wx_result['appid']
            result['partnerid'] = wx_result['mch_id']  # 商户号
            # 创建充值流水记录
            rf = MeObject('RechargeFlow')
            rf['user'] = self.user['_id']
            rf['recharge'] = coin_setting['price']
            rf['amount'] = coin_setting['amount']
            rf['os'] = coin_setting['os']
            rf['platform'] = 1  # 微信APP
            if channel:
                rf['channel'] = channel
            rf['version'] = version
            rf['status'] = 0
            rf['orderNo'] = out_trade_no
            rf['order'] = ''
            rf.save()
            self.write(result)
        else:
            self.write(ERR_PAY_CREATE_ORDERN0_ERROR.message)

    def recharge(self):
        '''
        添加充值记录
        :return: 
        '''
        try:
            obj = json.loads(self.request.body)
        except Exception, e:
            log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
            self.write(ERR_INVALID.message)
            return
        classHelper = ClassHelper("CoinSetting")
        coinSetting = classHelper.get(obj['id'])
        try:
            if coinSetting and coinSetting['status'] == 1:
                item = {}
                item['user'] = self.user['_id']
                item['recharge'] = coinSetting['amount'] * coinSetting['price']
                item['amount'] = coinSetting['amount']
                item['os'] = coinSetting['os']
                item['platform'] = coinSetting['platform']
                item['channel'] = obj['channel']
                item['version'] = obj['version']
                item['orderId'] = createOrderNo()
                classHelper = ClassHelper("RechargeFlow")
                reObj = classHelper.create(item)
                reObj['appleId'] = coinSetting['appleId']
                self.write(json.dumps(reObj, cls=MeEncoder))
            else:
                log.err("user %s appleRecharge error", self.user['_id'])
                self.write(ERR_PARA.message)
        except Exception, ex:
            log.err("user %s appleRecharge error", self.user['_id'])
            self.write(ERR_PARA.message)

    def payComplete(self):
        try:
            obj = json.loads(self.request.body)
        except Exception, e:
            log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
            self.write(ERR_INVALID.message)
            return

        # RechargeFlow的_id
        result = orderCallback(obj['_id'], self.user['_id'], obj['status'], obj['order'])
        if result:
            # self.write(json.dumps(result, cls=MeEncoder))
            self.write(ERR_SUCCESS.message)
        else:
            self.write(ERR_INVALID.message)

    def make_payment_info(self, out_trade_no=None, subject=None, total_amount=None, body=None, passback_params=None):
        public = {  # public args
            "app_id": alipay_config.appid,
            "method": "alipay.trade.app.pay",
            "charset": "utf-8",
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 2017-01-01 00:00:00
            "version": "1.0",
            "notify_url": "https://www.your-callback-url.com/callback/alipay",
            "sign_type": "RSA"
        }

        order_info = {"product_code": "QUICK_MSECURITY_PAY",
                      # 业务参数
                      "out_trade_no": None,
                      "subject": None,
                      "total_amount": total_amount,
                      "body": body,
                      }
        if not passback_params:
            order_info['passback_params'] = passback_params
        order_info["out_trade_no"] = "%s" % (out_trade_no)
        order_info["subject"] = "%s" % (subject)
        if total_amount <= 0.0:
            total_amount = 0.01
        order_info["total_amount"] = "%s" % (total_amount)

        public['biz_content'] = json.dumps(order_info, ensure_ascii=False)
        return public

    # 支付宝app支付
    def createAlipayAppOrder(self):
        logger.debug(self.jsonBody)
        obj = self.jsonBody
        coin_setting_id = obj.get('id')  # coinSettingId
        channel = obj.get('channel', '')
        version = obj.get('version', '')
        logger.debug('coin_setting_id: %s', coin_setting_id)
        coin_setting = MeObject('CoinSetting').get(coin_setting_id)
        logger.debug('coin_setting: %s', coin_setting)
        if coin_setting is None:
            # 未找到充值条目
            self.write(ERR_PAY_NOT_FIND_COIN_SETTING.message)
            return
        out_trade_no = PayUtil.createOrderNo()
        logger.debug('out_trade_no: %s', out_trade_no)

        total_fee = 0.01  # 这里将金额设为1分钱，方便测试
        body = '黑密虚拟商品-黑密滴' + str(coin_setting['amount']) + '个'
        subject = '黑密滴'
        payment_info = self.make_payment_info(out_trade_no=out_trade_no, subject=subject, total_amount=total_fee,
                                              body=body)
        res = alipay_core.make_payment_request(payment_info)
        result = {}
        result['code'] = 0
        result['res'] = res
        print res
        # 创建充值流水记录
        rf = MeObject('RechargeFlow')
        rf['user'] = self.user['_id']
        rf['recharge'] = coin_setting['price']
        rf['amount'] = coin_setting['amount']
        rf['os'] = coin_setting['os']
        rf['platform'] = 0  # 支付宝APP
        if channel:
            rf['channel'] = channel
        rf['version'] = version
        rf['status'] = 0
        rf['orderNo'] = out_trade_no
        rf['order'] = ''
        rf.save()
        self.write(result)
