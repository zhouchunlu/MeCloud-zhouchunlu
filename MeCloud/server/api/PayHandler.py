# coding=utf8
import traceback
import uuid
import json
import time
import copy
import tornado.httpclient
import tornado.web
import requests
from api.BaseHandler import BaseHandler, MeQuery, MeObject, BaseConfig


from helper.ClassHelper import ClassHelper
from helper.Util import MeEncoder
from lib import log
from model.MeError import *
import datetime

from lib import payUtil

withdrawRate = 0.05  # 黑蜜滴比人民币
contributorRate = 0.7  # 贡献者比例
faceOwnerRate = 0.3  # 认领者比例
systemRax = 0.1  # 系统抽成比例

sandboxUrl = "https://sandbox.itunes.apple.com/verifyReceipt"
buyUrl = "https://buy.itunes.apple.com/verifyReceipt"


class PayHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, classname=None):
        # 查看钱包余额
        if classname not in ['wallet']:
            self.write(ERR_PATH_PERMISSION.message)
            return
        query = {
            'user': self.user['_id']
        }
        obj = {
            'user': self.user['_id'].decode(),
            'balance': 0,
            'income': 0
        }
        if not self.check_field('Wallet', obj):
            return
        walletHelper = ClassHelper("Wallet")
        objects = walletHelper.findCreate(query, obj)
        self.filter_field(objects)
        self.write(json.dumps(objects, cls=MeEncoder))

    @tornado.web.authenticated
    def post(self, action=None):
        log.debug('action:%s', action)
        try:
            if action == 'createWxAppOrder':
                pass
            elif action == 'createAppleAppOrder':
                self.createAppleAppOrder()
            elif action == 'completeAppleAppOrder':
                self.completeAppleAppOrder()
            elif action == 'createAlipayAppOrder':
                self.createAlipayAppOrder()
            elif action == 'charge':  # 消费
                self.charge()
            else:
                print "action error: " + action
        except Exception, e:
            print e
            msg = traceback.format_exc()
            print msg
            self.write(ERR_PARA.message)

    # 创建订单号
    def createOrderNo(self):
        return str(uuid.uuid4()).replace('-', '')

    # # 支付完成的回调
    # def orderCallback(self, oId, userId, status, order):
    #     '''
    #     根据支付结果更新订单的状态
    #     :param oId:RechargeFlow Id
    #     :param userId:用户Id
    #     :param status: 支付是否成功，1为成功，3为等待验证
    #     :param order:第三方平台返回订单信息，包括错误码
    #     :return:
    #     '''

    #     ###更新充值流水记录
    #     orderHelper = ClassHelper("RechargeFlow")
    #     rechargeFlow = orderHelper.get(oId)
    #     walletHelper = ClassHelper("Wallet")
    #     walletInfo = walletHelper.find_one({"user": userId})
    #     if status == 1:  # 充值成功,更新钱包
    #         rechargeFlow_action = {'destClass': 'RechargeFlow',
    #                                'query': {"_id": oId},
    #                                'action': {"@set": {"status": status, "order": order}}}
    #         if not walletInfo:  # 未找到钱包直接创建
    #             wallet = {"user": userId, 'balance': rechargeFlow['amount']}
    #             walletInfo = walletHelper.create(wallet, transaction=[rechargeFlow_action])
    #         else:
    #             wallet = {
    #                 "$inc": {'balance': rechargeFlow['amount']}
    #             }
    #             walletInfo = walletHelper.update(walletInfo['_id'], wallet, transaction=[rechargeFlow_action])
    #             return walletInfo
    #     else:
    #         rechargeFlow = orderHelper.update(oId, {"$set": {"status": status, "order": order}})
    #         return rechargeFlow



    # 苹果支付下单
    def createAppleAppOrder(self):
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
                item['recharge'] = coinSetting['price']
                item['amount'] = coinSetting['amount'] + coinSetting['free']
                item['os'] = coinSetting['os']
                item['platform'] = coinSetting['platform']
                try:
                    item['channel'] = self.request.headers.get("X-MeCloud-Channel", None)
                    item['version'] = self.request.headers.get("X-MeCloud-Client", None)
                except:
                    pass
                item['orderNo'] = self.createOrderNo()
                item['status'] = 0
                classHelper = ClassHelper("RechargeFlow")
                reObj = classHelper.create(item)
                self.write(json.dumps({'_id': reObj['_id'], 'appleId': coinSetting['appleId']}, cls=MeEncoder))
            else:
                log.err("user %s appleRecharge error", self.user['_id'])
                self.write(ERR_PARA.message)
        except Exception, ex:
            log.err("user %s appleRecharge error:%s", self.user['_id'], ex)
            self.write(ERR_PARA.message)

    # 苹果支付状态上传服务器
    def completeAppleAppOrder(self):
        try:
            obj = json.loads(self.request.body)
        except Exception, e:
            log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
            self.write(ERR_INVALID.message)
            return
        try:
            certificate = obj.get('certificate', None)
            if certificate:
                result = self.appleVerify(buyUrl, sandboxUrl, {"receipt-data": certificate}, 1)
                order = {
                    'code': obj.get('code', None),
                    "certificate": obj.get('certificate', None),
                    "appleOrderNo": obj.get('appleOrderNo', None),
                    "certificateInfo": result,
                    "status": obj['status']
                }
                if result['status'] == 0:  # =0更新钱包和创建充值记录，否则只更新充值记录不更新钱包
                    item = payUtil.orderCallback(obj['id'], self.user['_id'], 1, order)
                else:
                    item = payUtil.orderCallback(obj['id'], self.user['_id'], 3, order)
                if item:
                    self.write(ERR_SUCCESS.message)
                else:
                    self.write(ERR_INVALID.message)
            else:
                self.write(ERR_APPLE_CERTIFICATE.message)
                return
        except Exception, e:
            log.err("PayHandler-->orderCallback in payComplete() error, %s", e)
            self.write(e.message)


    # 支付宝app支付
    def createAlipayAppOrder(self):
        print self.jsonBody
        obj = self.jsonBody
        coin_setting_id = obj.get('id')  # coinSettingId
        # channel = obj.get('channel', '')
        # version = obj.get('version', '')

        channel = self.request.headers.get("X-MeCloud-Channel", None)
        version = self.request.headers.get("X-MeCloud-Client", None)

        log.debug('coin_setting_id: %s', coin_setting_id)
        coin_setting = MeObject('CoinSetting').get(coin_setting_id)
        log.debug('coin_setting: %s', coin_setting)
        if coin_setting is None:
            # 未找到充值条目
            self.write(ERR_PARA.message)
            return
        out_trade_no = self.createOrderNo()
        log.debug('out_trade_no: %s', out_trade_no)

        total_fee = 0.01  # 这里将金额设为1分钱，方便测试
        body = '黑密虚拟商品-黑密滴' + str(coin_setting['amount']) + '个'
        subject = '黑密滴'
        payment_info = self.make_payment_info(out_trade_no=out_trade_no, subject=subject, total_amount=total_fee,
                                              body=body)
        log.debug('payment_info:%s', payment_info)
        res = alipay_core.make_payment_request(payment_info)
        result = {}
        result['code'] = 0
        result['errCode'] = 0
        result['res'] = res
        # result['res']='xxxx'
        log.debug('res:%s', res)
        log.debug('result res:%s', result['res'])
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

    # 消费，付费购买
    def charge(self):
        '''
        obj = {'id':Goods_id:True,'chargeFlowId':ChargeFlow_id:False} chargeFlowId是在重新发起支付时需要传递
        :return: 
        '''
        try:
            obj = json.loads(self.request.body)
        except Exception, e:
            log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
            self.write(ERR_INVALID.message)
            return
        goodHelper = ClassHelper('Goods')
        good = goodHelper.find_one({'_id': obj['id']})
        walletHelper = ClassHelper('Wallet')
        wallet = walletHelper.find_one({'user': self.user['_id']})
        if not wallet:
            self.write(ERR_ACCOUNT_BALANCE.message)
            return
        if good and wallet:
            # 添加消费记录，状态未支付
            chargeFlowHelper = ClassHelper('ChargeFlow')
            if 'chargeFlowId' not in obj:
                chargeFlow = {
                    'user': self.user['_id'].decode(),
                    'amount': good['price'],
                    'goods': good['_id'].decode(),
                    'status': 0
                }
                chargeFlow = self.check_field('ChargeFlow', chargeFlow)
                if not chargeFlow:
                    return
                chargeFlow = chargeFlowHelper.create(chargeFlow)
            else:
                chargeFlow = chargeFlowHelper.find_one({'_id': obj['chargeFlowId']})
            if not chargeFlow:
                self.write(ERR_ACCOUNT_GOODS.message)
                return
            # 扣款并更新消费记录状态为已支付
            if wallet.get('balance', 0) >= good['price'] and chargeFlow:
                item = {
                    "$inc": {'balance': -good['price']}
                }
                face = ClassHelper('Face').get(good['goods'])
                actions = None
                uploader_income_show = ''
                owner_income_show = ''
                if face:
                    # 计算收益
                    # print 'owner,uploader:', face['assign']['user'], face['uploader']
                    print 'price:', good['price']
                    uploder_income = good['price'] * withdrawRate * contributorRate * (1 - systemRax)
                    owner_income = good['price'] * withdrawRate * faceOwnerRate * (1 - systemRax)
                    # print 'float uploder_income, owner_income:', uploder_income, owner_income
                    uploder_income = int(uploder_income * 100)
                    owner_income = int(owner_income * 100)
                    print 'int uploader_income, owner_income:', uploder_income, owner_income
                    uploader_income_show = str(float(uploder_income) / 100)
                    owner_income_show = str(float(owner_income) / 100)
                    # print 'show uploader_income, owner_income:', uploader_income_show, owner_income_show
                    uploader_wallet_action = {'destClass': 'Wallet', 'query': {'user': face['uploader']},
                                              'action': {'@inc': {'income': uploder_income}}}
                    owner_wallet_action = {'destClass': 'Wallet', 'query': {'user': face['assign']['user']},
                                           'action': {'@inc': {'income': owner_income}}}
                    chargeFlow_action = {'destClass': 'ChargeFlow', 'query': {'_id': chargeFlow['_id']},
                                         'action': {'@set': {'status': 1}}}
                    actions = [uploader_wallet_action, owner_wallet_action, chargeFlow_action]
                    # 计入收益记录
                    user_info = ClassHelper('UserInfo').find_one({'user': self.user['_id']})
                    owner_income_flow = {}
                    owner_income_flow['consumer_id'] = self.user['_id']
                    owner_income_flow['consumer_nickname'] = user_info['nickName']
                    owner_income_flow['consumer_avatar'] = user_info.get('avatar', None)
                    owner_income_flow['coin'] = good['price']
                    owner_income_flow['income'] = int(float(owner_income_show) * 100)
                    owner_income_flow['reason'] = 'owner'
                    owner_income_flow['user'] = face['assign']['user']
                    owner_income_flow['charge_flow'] = chargeFlow['_id']
                    owner_income_flow_action = {'destClass': 'StatCount',
                                                'query': {'name': 'newIncome_' + face['assign']['user']},
                                                'action': {'@inc': {'count': 1}}}
                    ClassHelper('IncomeFlow').create(obj=owner_income_flow, transaction=[owner_income_flow_action])

                    uploader_income_flow = {}
                    uploader_income_flow['consumer_id'] = self.user['_id']
                    uploader_income_flow['consumer_nickname'] = user_info['nickName']
                    uploader_income_flow['consumer_avatar'] = user_info.get('avatar', None)
                    uploader_income_flow['coin'] = good['price']
                    uploader_income_flow['income'] = int(float(uploader_income_show) * 100)
                    uploader_income_flow['reason'] = 'uploader'
                    uploader_income_flow['user'] = face['uploader']
                    uploader_income_flow['charge_flow'] = chargeFlow['_id']
                    uploader_income_flow_action = {'destClass': 'StatCount',
                                                   'query': {'name': 'newIncome_' + face['uploader']},
                                                   'action': {'@inc': {'count': 1}}}
                    ClassHelper('IncomeFlow').create(obj=uploader_income_flow,
                                                     transaction=[uploader_income_flow_action])

                wallet = walletHelper.update(wallet['_id'], item,
                                             transaction=actions)
                if wallet:
                    # result = chargeFlowHelper.update(chargeFlow['_id'], {'$set': {'status': 1}})
                    # self.filter_field(result)
                    data = copy.deepcopy(ERR_SUCCESS)
                    data.message['mosaic'] = 1
                    self.write(json.dumps(data.message, cls=MeEncoder))
                    #
                    self.pushMessage(good, owner_income_show, uploader_income_show)
                    # 添加feed记录
                    # addFeedRecord(self.user['_id'], 'charge', face['_id'])
                    # print 'send pay push'
                    # t = threading.Thread(target=self.pushMessage,
                    #                      args=(good,))
                    # t.setDaemon(True)
                    # t.start()
                    # print 'pay finish'
                else:  # 扣费失败，但是已创建消费记录
                    data = copy.deepcopy(ERR_ACCOUNT_WALLET)
                    # data.message['data'] = self.filter_field(chargeFlow)
                    self.write(json.dumps(data.message, cls=MeEncoder))
            else:  # 账户余额不足，但是已创建消费记录
                data = copy.deepcopy(ERR_ACCOUNT_BALANCE)
                # data.message['data'] = self.filter_field(chargeFlow)
                self.write(json.dumps(data.message, cls=MeEncoder))
        else:  # 无法获取商品
            self.write(ERR_ACCOUNT_GOODS.message)

    @tornado.web.asynchronous
    def pushMessage(self, good, owner_income_show, uploader_income_show):
        '''
        author:arther
        '''
        log.debug('good:%s', good)

        def callback(response):
            log.info('Push:%s', response.body)
            self.finish()

        pushUrl = BaseConfig.pushUrl
        face = ClassHelper('Face').get(good['goods'])
        if face:
            if self.user['_id'] != face['assign']['user']:
                ##ownedBought 购买了我主页的照片 排除掉照片主人购买自身主页照片的情况
                ownedBoughtPushData = {
                    'userid': face['assign']['user'],
                    'action': 'ownedBought',
                    'otherid': self.user['_id'],
                    'extra': owner_income_show
                }
                client = tornado.httpclient.AsyncHTTPClient()
                client.fetch(pushUrl, callback=callback, method="POST", body=json.dumps(ownedBoughtPushData),
                             headers={'X-MeCloud-Debug': '1'})
            ##assignedBought 购买了我共享的照片
            assignedBoughtPushData = {
                'userid': face['assign']['assigner'],
                'action': 'assignedBought',
                'otherid': self.user['_id'],
                'extra': uploader_income_show
            }
            client = tornado.httpclient.AsyncHTTPClient()
            client.fetch(pushUrl, callback=callback, method="POST", body=json.dumps(assignedBoughtPushData),
                         headers={'X-MeCloud-Debug': '1'})

    ### 苹果验证服务
    def appleVerify(self, url, testUrl, data, count=3):
        r = requests.post(url, data=json.dumps(data))
        result = json.loads(r.text)
        if result:
            if result['status'] == 0:  # 正式服验证成功
                return result
            elif result['status'] == 21007:  # 在测试服
                return self.appleVerify(testUrl, url, data, count=1)
            else:
                return result
                # elif result['status'] == 21000:
                #     count = count + 1
                #     self.appleVerify(url, testUrl, data, count)
        else:  # 无数据返回
            if count > 2:  # 三次验证
                return result
            else:
                count = count + 1
                return self.appleVerify(url, testUrl, data, count)
