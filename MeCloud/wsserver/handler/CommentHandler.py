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


# 评论
class CommentHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, action=None):
        if action == 'unreadList':
            self.unreadList()
        elif action == 'unreadListByFromId':
            self.unreadListByFromId()
        elif action == 'listByFromId':
            self.listByFromId()
        else:
            print "action error: " + action

    @tornado.web.authenticated
    def post(self, action=None):
        if action == 'send':
            self.send()
        elif action == 'read':
            self.read()
        else:
            print "action error: " + action

    # 发消息(评论)
    def send(self):
        try:
            logger.debug(self.jsonBody)
            obj = self.jsonBody
            logger.debug('to_id:' + obj.get('to_id'))
            logger.debug('c: %s', obj.get('c'))
            logger.debug('c_type: %s', obj.get('c_type'))
            logger.debug('m_id: %s', obj.get('m_id'))
            media_id = obj.get('m_id')
            from_id = self.user['_id']
            logger.debug('from_id: %s', from_id)
            user_query = MeQuery("UserInfo")
            user_info = user_query.find_one({'user': from_id})
            message_dict = {'from_id': from_id, 'c': obj.get('c'), 'to_id': obj.get('to_id'),
                            'c_type': obj.get('c_type'), 'msg_type': 2, 'from_avatar': user_info['avatar'], 'from_name'
                            : user_info['nickName'], 'status': 0, 'm_id': media_id}
            message = MeObject('Message', obj=message_dict)
            message.save()
            # 格式化时间为long型
            message_dict['create_at'] = long(message['createAt'].strftime('%s')) * 1000
            message_dict['t'] = 'comment'
            message_dict['id'] = message['_id']
            message_json = json.dumps(message_dict, ensure_ascii=False)
            logger.debug(message_json)
            print type(message['createAt'])
            rc = RedisDb.get_connection()
            rc.publish(Constants.REDIS_CHANNEL_FOR_PUSH, message_json)
            # 发push
            push_cid_obj = ClassHelper('PushCid').find_one({'userid': obj.get('to_id')})
            logger.debug('push_cid_obj: %s', push_cid_obj)
            if push_cid_obj:
                # push_cid = MeObject('PushCid', obj=push_cid_obj)
                title = user_info['nickName']
                content = '新评论'
                data = 'honey://comment/' + from_id + '?m_id=' + media_id
                print title.encode('utf-8')
                print content.encode('utf-8')
                t = threading.Thread(target=MyGtUtil.pushMessageToSingle,
                                     args=(push_cid_obj['cid'], title.encode('utf-8'), content.encode('utf-8'), data,))
                t.setDaemon(True)
                t.start()
            # logger.debug(ERR_SUCCESS.message)
            r = {}
            r['id'] = message['_id']
            r['code'] = 0
            r['create_at'] = message_dict['create_at']
            self.write(r)
        except Exception, e:
            logger.error(e)
            msg = traceback.format_exc()
            logger.error(msg)
            self.write(ERR_PARA.message)

    # 每个人最新的未读评论列表 (session列表)
    def unreadList(self):
        try:
            logger.debug('self.userid: %s:', self.user['_id'])
            all = int(self.get_argument('all', 0))
            logger.debug('all: %s', all)
            if all == 1:
                match = {"$match": {"to_id": self.user['_id'],
                                    "msg_type": 2}}
            else:
                match = {"$match": {"to_id": self.user['_id'],
                                    "status": 0, "msg_type": 2}}
            # "59ca0b46ca714306705996dc"
            message_query = MeQuery("Message")
            unread_list = message_query.aggregate([match,
                                                   {"$group": {"_id": {"from_id": "$from_id", "m_id": "$m_id"},
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
                                                                   "$last": "$t"
                                                                            "o_id"},
                                                               "from_avatar": {
                                                                   "$last": "$from_avatar"},
                                                               "m_id": {
                                                                   "$last": "$m_id"}
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

    # 一个人的未读评论列表
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
            m_id = self.get_argument('m_id')
            logger.debug('from_id: %s, m_id: %s', from_id, m_id)
            # if msg_id:
            #     query = {"to_id": to_id, "status": 0,
            #              "_id": {"$lt": ObjectId(msg_id)}}
            # else:
            #     query = {"to_id": to_id, "status": 0}
            query = {"to_id": to_id, "status": 0, "from_id": from_id, "msg_type": 2, "m_id": m_id}
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
    def read(self):
        obj = self.jsonBody
        from_id = obj.get('from_id')
        m_id = obj.get('m_id')
        message_id = obj.get('message_id')
        # message_id = '59db35da51159a0e1b5145de' #for test args
        helper = ClassHelper('Message')
        r = helper.db.update_many('Message',
                                  {'_id': {'$lte': ObjectId(message_id)}, 'status': 0, 'from_id': from_id,
                                   'msg_type': 2,
                                   'm_id': m_id},
                                  {'$set': {"status": 1}})
        logger.debug('read comment r:%s', r)
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

    # 该照片所有历史的评论根据发起者查询（包括照片所有者自己的评论和已读评论）
    def listByFromId(self):
        try:
            # test msg_id
            # ObjectId("59dc380051159a123fe8a230")
            message_id = self.get_argument('message_id', default=None)
            count = int(self.get_argument('count', default=20))
            logger.debug("count: %s", count)
            if count > 50:
                count = 50
            logger.debug("message_id: %s, count: %s", message_id, count)
            # print self.user['_id']
            # to_id = "59ca0b46ca714306705996dc"
            to_id = self.user['_id']
            from_id = self.get_argument('from_id')
            m_id = self.get_argument('m_id')
            logger.debug('from_id: %s, m_id: %s', from_id, m_id)
            if message_id:
                # query = {"to_id": to_id, "status": 0,
                #          "_id": {"$lt": ObjectId(msg_id)}}
                query = {"$or": [{"to_id": to_id, "from_id": from_id}, {"to_id": from_id, "from_id": to_id}],
                         "status": 0,
                         "msg_type": 2, "m_id": m_id, "_id": {"$lt": ObjectId(message_id)}}
            else:
                query = {"$or": [{"to_id": to_id, "from_id": from_id}, {"to_id": from_id, "from_id": to_id}],
                         "status": 0,
                         "msg_type": 2, "m_id": m_id}
            logger.debug('query: %s', query)
            helper = ClassHelper('Message')
            unread_list = helper.find(query, limit=count)
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
