# coding=utf8
import json
import threading
import traceback

import tornado.web
from mecloud.api.BaseHandler import BaseHandler, ERR_PARA, ERR_SUCCESS, MeObject, MeQuery, datetime, date, ObjectId, \
    ClassHelper
from mecloud.helper.RedisHelper import RedisDb

from getui import MyGtUtil
from util import RedisUtil
from ws import Constants
from wsserver import logger


class PushHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, action=None):
        if action == 'unreadList':
            self.unreadList()
        elif action == 'unreadListByFromId':
            self.unreadListByFromId()

    @tornado.web.authenticated
    def post(self, action=None):
        if action == 'sendMessage':
            self.sendMessage()
        elif action == 'readMessage':
            self.readMessage()
        else:
            print "action error: " + action

    # 发消息
    def sendMessage(self):
        try:
            logger.debug(self.jsonBody)
            # cookie = self.get_cookie("u")
            # logger.debug('cookie:' + cookie)
            # from_uid = RedisUtil.getUid(cookie)
            # # print from_uid
            # if not from_uid:
            #     logger.error('无效cookie')
            #     self.write(ERR_PARA.message)
            #     return
            obj = self.jsonBody
            from_id = self.user['_id']
            logger.debug('from_id:%s', from_id)
            user_query = MeQuery("UserInfo")
            user_info = user_query.find_one({'user': from_id})
            message_dict = {'from_id': from_id, 'c': obj.get('c'), 'to_id': obj.get('to_id'),
                            'c_type': obj.get('c_type'), 'msg_type': 0, 'from_avatar': user_info['avatar'], 'from_name'
                            : user_info['nickName'], 'status': 0}
            logger.debug('to_id:' + obj.get('to_id'))
            logger.debug('c: %s', obj.get('c'))
            logger.debug('c_type: %s', obj.get('c_type'))
            message = MeObject('Message', obj=message_dict)
            message.save()
            # 格式化时间为long型
            message_dict['create_at'] = long(message['createAt'].strftime('%s')) * 1000
            message_dict['t'] = 'message'
            message_dict['id'] = message['_id']
            message_json = json.dumps(message_dict, ensure_ascii=False)
            logger.debug(message_json)
            # message_json. = long(message['createAt'].strftime('%s')) * 1000
            print type(message['createAt'])
            rc = RedisDb.get_connection()
            rc.publish(Constants.REDIS_CHANNEL_FOR_PUSH, message_json)
            # logger.debug(ERR_SUCCESS.message)
            # 发push
            push_cid_obj = ClassHelper('PushCid').find_one({'userid': obj.get('to_id')})
            logger.debug('push_cid_obj: %s', push_cid_obj)
            if push_cid_obj:
                # push_cid = MeObject('PushCid', obj=push_cid_obj)
                title = user_info['nickName']
                content = '新私信'
                data = 'honey://message/' + from_id
                print title.encode('utf-8')
                print content.encode('utf-8')
                t = threading.Thread(target=MyGtUtil.pushMessageToSingle,
                                     args=(push_cid_obj['cid'], title.encode('utf-8'), content.encode('utf-8'), data,))
                t.setDaemon(True)
                t.start()
            r = {}
            r['id'] = message['_id']
            r['code'] = 0
            r['create_at'] = message_dict['create_at']
            logger.debug('r: %s', r)
            self.write(r)
        except Exception, e:
            logger.error(e)
            msg = traceback.format_exc()
            logger.error(msg)
            self.write(ERR_PARA.message)

    # 每个人最新的未读消息列表
    def unreadList(self):
        try:
            # print self.user['_id']
            logger.debug('to_id:%s', self.user['_id'])
            # "59ca0b46ca714306705996dc"
            message_query = MeQuery("Message")
            unread_list = message_query.aggregate([{"$match": {"to_id": self.user['_id'],
                                                               "status": 0, "msg_type": 0}},
                                                   {"$group": {"_id": "$from_id",
                                                               "count": {"$sum": 1},
                                                               "c": {"$last": "$c"},
                                                               "id": {"$last": "$_id"},
                                                               "create_at": {
                                                                   "$last": "$createAt"},
                                                               "c_type": {
                                                                   "$last": "$c_type"},
                                                               "status": {
                                                                   "$last": "$status"},
                                                               "from_name": {
                                                                   "$last": "$from_name"},
                                                               "msg_type": {
                                                                   "$last": "$msg_type"},
                                                               "from_id": {
                                                                   "$last": "$from_id"},
                                                               "to_id": {
                                                                   "$last": "$to_id"},
                                                               "from_avatar": {
                                                                   "$last": "$from_avatar"}
                                                               }},
                                                   {"$sort": {"create_at": -1}}])  # 时间倒序
            logger.debug(unread_list)
            # 整理数据
            if unread_list:
                for unread_msg in unread_list:
                    del unread_msg['_id']
                    # print type(unread_msg['id'])
                    # print str(unread_msg['id'])
                    # 转换objectId to string
                    unread_msg['id'] = str(unread_msg['id'])
                    # print type(unread_msg['create_at'])
                    unread_msg['create_at'] = long(unread_msg['create_at'].strftime('%s')) * 1000
            result = {}
            result['errCode'] = 0
            result['unread_list'] = unread_list
            self.write(json.dumps(result, ensure_ascii=False))  # , cls=CJsonEncoder #格式化时间
        except Exception, e:
            logger.error(e)
            msg = traceback.format_exc()
            logger.error(msg)
            self.write(ERR_PARA.message)

    # 每个人最新的未读消息列表
    def unreadListByFromId(self):
        try:
            # test msg_id
            # ObjectId("59dc380051159a123fe8a230")
            # msg_id = self.get_argument('id')
            # logger.debug("id: %s", msg_id)
            print self.user['_id']
            # to_id = "59ca0b46ca714306705996dc"
            to_id = self.user['_id']
            from_id = self.get_argument('from_id')
            # if msg_id:
            #     query = {"to_id": to_id, "status": 0,
            #              "_id": {"$lt": ObjectId(msg_id)}}
            # else:
            #     query = {"to_id": to_id, "status": 0}
            query = {"to_id": to_id, "status": 0, "from_id": from_id, "msg_type": 0}
            print query
            helper = ClassHelper('Message')
            unread_list = helper.find(query)
            logger.debug(unread_list)
            print unread_list.__len__()
            if unread_list:
                for unread_msg in unread_list:
                    unread_msg['id'] = unread_msg['_id']
                    unread_msg['create_at'] = long(unread_msg['createAt'].strftime('%s')) * 1000
                    del unread_msg['_id']
                    if unread_msg.get('acl', None) is not None:
                        del unread_msg['acl']
                    del unread_msg['createAt']
                    del unread_msg['updateAt']
            result = {}
            result['errCode'] = 0
            result['unread_list'] = unread_list
            self.write(json.dumps(result, ensure_ascii=False))  # , cls=CJsonEncoder #格式化时间
        except Exception, e:
            logger.error(e)
            msg = traceback.format_exc()
            logger.error(msg)
            self.write(ERR_PARA.message)

    # 标记消息已读 message_id为客户端收到的最大的message_id
    def readMessage(self):
        obj = self.jsonBody
        from_id = obj.get('from_id')
        to_id = self.user['_id']
        message_id = obj.get('message_id')
        logger.debug('from_id: %s, message_id: %s', from_id, message_id)
        # message_id = '59db35da51159a0e1b5145de' #for test args
        helper = ClassHelper('Message')

        r = helper.db.update_many('Message',
                                  {'_id': {'$lte': ObjectId(message_id)}, 'status': 0, 'from_id': from_id,
                                   'msg_type': 0,
                                   'to_id': to_id},
                                  {'$set': {"status": 1}})
        logger.debug('read message update r: %s', r)
        self.write(ERR_SUCCESS.message)

    # 格式化时间方法
    class CJsonEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(obj, date):
                return obj.strftime('%Y-%m-%d')
            else:
                return json.JSONEncoder.default(self, obj)
            pass
