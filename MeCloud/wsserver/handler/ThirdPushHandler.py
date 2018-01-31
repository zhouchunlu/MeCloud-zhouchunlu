# coding=utf8
import traceback

import tornado.web
from mecloud.api.BaseHandler import BaseHandler, ERR_PARA, MeObject, ClassHelper, json, MeQuery
from mecloud.helper.RedisHelper import RedisDb

from getui import PushUtil, MyGtUtil
from util.PushUriConfig import action_uri_dict
from ws import Constants
from wsserver import logger


# action_uri_dict = {'assigned': '/assigned', 'claimed': '/claimed', 'followed': '/followed',
#                    'assignedBought': '/assignedBought','ownedBought': '/ownedBought','message': '/message', 'comment': 'comment'}


class ThirdPushHandler(BaseHandler):
    # 根据action获取push的主标题　副标题　内容
    def getNotifyContent(self, action, otherid):
        nickname = ''
        if otherid:
            other_user1 = MeQuery('UserInfo').find_one({'user': otherid})
            if other_user1:
                nickname = other_user1['nickName']
        if action == 'followed':
            title = '新粉丝'
            content = nickname + '关注了你'
            # content = '新粉丝'
        elif action == 'assigned':
            title = nickname
            content = '给你贡献了1张照片,快来看~'
            # content = '有人给我贡献照片'
        elif action == 'claimed':
            title = nickname
            content = '认领了你贡献的照片'
            # content = '有人认领了我贡献的照片'
        elif action == 'assignedBought':
            title = '新的收益'
            content = nickname + '付费查看了你贡献的照片'
            # content = '有人购买了我贡献的照片'
        elif action == 'ownedBought':
            title = '新的收益'
            content = nickname + '付费查看了你的照片'
            # content = '有人购买了我主页的照片'
        else:
            logger.warn('push action error:%s', action)
            return None
        return {'title': title, 'content': content}

    @tornado.web.authenticated
    def get(self, action=None):
        pass

    # @tornado.web.authenticated
    def post(self, action=None):
        if action == 'push':
            self.push()
        else:
            print "action error: " + action

    # 个推push
    def push(self):
        try:
            userid = self.jsonBody['userid']
            otherid = self.jsonBody['otherid']
            action = self.jsonBody.get('action')
            logger.debug('userid: %s, otherid: %s, action: %s', userid, otherid, action)
            if userid is None or action is None or otherid is None:
                self.write(ERR_PARA.message)
                return
            uri = action_uri_dict.get(action, None)
            if uri is None:
                self.write(ERR_PARA.message)
                return
            uri = 'honey://' + uri
            logger.debug('uri: %s', uri)
            if action == 'claimed':
                uri = uri + '/' + otherid
            notify_content = self.getNotifyContent(action, otherid)
            logger.debug('notify_content: %s', notify_content)
            if notify_content is None:
                self.write(ERR_PARA.message)
                return
            # 长链接通知
            message_dict = {'t': 'notify'}
            message_dict['title1'] = notify_content['title']
            # message_dict['title2'] = notify_content['title2']
            message_dict['title2'] = notify_content['content']
            message_dict['to_id'] = userid
            message_dict['uri'] = uri
            message_json = json.dumps(message_dict, ensure_ascii=False)
            logger.debug(message_json)
            rc = RedisDb.get_connection()
            publish_result = rc.publish(Constants.REDIS_CHANNEL_FOR_PUSH, message_json)
            logger.debug('public_result: %s', publish_result)
            push_cid_obj = ClassHelper('PushCid').find_one({'userid': userid})
            logger.debug('push_cid_obj: %s', push_cid_obj)
            if push_cid_obj is None:
                # 没有找到对应的push_cid
                self.write(ERR_PARA.message)
                return
            push_cid = MeObject('PushCid', obj=push_cid_obj)
            result = MyGtUtil.pushMessageToSingle(push_cid['cid'], notify_content['title'].decode("utf-8"),
                                                  notify_content['content'].decode("utf-8"), data=uri)
            logger.debug('result:%s', result)
            # result = PushUtil.pushMessageToSingle()
            self.write(result)
        except Exception, e:
            logger.error(e)
            msg = traceback.format_exc()
            logger.error(msg)
            self.write(ERR_PARA.message)
