#!/user/bin/env python
# encoding: utf-8
'''
@author: Dong Jun
@file:   FollowerHandler.py
@time:   2017/9/21  21:12
'''

import json
import tornado.web
from copy import deepcopy
from bson import ObjectId
from api.BaseHandler import BaseHandler, BaseConfig
from helper.ClassHelper import ClassHelper
from helper.Util import MeEncoder
from lib import log
from model.MeError import *
from api.CountHandler import getIFCCount
from helper.FollowHelper import *



class FollowerHandler(BaseHandler):
    # def __init__(self):
    #     super(FollowerHandler, self).__init__()

    @tornado.web.authenticated
    def get(self, userId, count, isuser=1):

        faceHelper = ClassHelper('FaceRecommend')
        isExistBackupUser = False
        field_name = 'user'
        if int(isuser) == 0:
            field_name = 'backupUser'
            isExistBackupUser = True

        oid = self.get_argument('objectId', None)
        if oid:
            query = {field_name: userId, 'read': {'$exists': False}, 'backupUser': {'$exists': isExistBackupUser},
                     '_id': {'$lt': oid}}
        else:
            query = {field_name: userId, 'read': {'$exists': False}, 'backupUser': {'$exists': isExistBackupUser}}



        sort = {'_id': -1}
        fs = faceHelper.find(query, sort=sort, limit=int(count))
        faces = []
        for face in fs:
            if face.has_key('createAt'):
                del (face['createAt'])
            del (face['updateAt'])
            del (face['acl'])
            if face.has_key('backupUser'):
                face['user'] = face['backupUser']
                del (face['backupUser'])

            face['mosaic'] = 5
            faces.append(face)

        result = deepcopy(ERR_SUCCESS.message)
        result['data'] = faces
        result['count'] = faceHelper.query_count({'user': userId})
        result['unread'] = faceHelper.query_count({'user': userId, 'read': {'$exists': False}})
        print result
        self.write(result)

    @tornado.web.authenticated
    def post(self, action=None, followee=None, isuser=1):
        userId = self.get_current_user()
        if not userId:
            log.err("follow error,user not exist!")
            self.write(ERR_USER_NOTFOUND.message)
            return

        if not followee:
            log.err("request param error")
            self.write(ERR_NOPARA.message)
            return

        is_user = True
        if int(isuser) == 0:
            is_user = False

        # 查找用户是否存在
        if is_user == True:
            userHelper = ClassHelper( "User" )
        else:
            userHelper = ClassHelper( "BackupUser" )
        findUser = userHelper.find_one( {'_sid': followee} )
        if not findUser:
            log.err( "%s error,followee not exist!",action)
            self.write( ERR_USER_NOTFOUND.message )
            return

        blackHelper = ClassHelper( "Blacklist" )
        if action == 'follow':
            blacked = blackHelper.find_one( {'user': userId, 'blacker': followee} )
            isblacked = blackHelper.find_one( {'user': followee, 'blacker': userId} )
            if blacked:
                self.write( ERR_BLACKED_PERMISSION.message )
                return
            if isblacked:
                self.write( ERR_BEBLACKED_PERMISSION.message )
                return

        if is_user:
            fieldname = "followee"
        else:
            fieldname = "backupFollowee"
        followHelper = ClassHelper("Followee")

        try:
            if action == 'follow':  # 关注
                # 判断是否已经关注过
                followed = followHelper.find_one( {'user': userId, fieldname: followee, 'effect': {'$gte': 0}} )
                if followed and followed['effect']>=1:
                    self.write( ERR_SUCCESS.message )
                    return
                FollowHelper.follow(userId, followee, is_user)
                fr = followHelper.find_one( {'user': userId, fieldname: followee, 'effect': {'$gte': 1}},
                                            {'acl': 0, 'createAt': 0, '_sid': 0} )
                fr['relationStatus']=fr['effect']
                del fr['effect']
                del fr['_id']

                if fr.has_key('backupFollowee'):
                    del fr['backupFollowee']
                    fr['isUser'] = 0
                else:
                    del fr['followee']
                    fr['isUser'] = 1

                successInfo = deepcopy( ERR_SUCCESS )
                successInfo.message["data"] = fr
                self.write( json.dumps( successInfo.message, cls=MeEncoder ) )
            elif action == 'unfollow':  # 取消关注
                # 之前未关注过或者已经取消关注，直接返回
                unfollowed = followHelper.find_one( {'user': userId, fieldname: followee, 'effect': {'$gte': 1}} )
                if not unfollowed:
                    self.write( ERR_SUCCESS.message )
                    return
                FollowHelper.unfollow(userId, followee, is_user)
                fr = followHelper.find_one( {'user': userId, fieldname: followee, 'effect': {'$gte': 0}},
                                            {'acl': 0, 'createAt': 0, '_sid': 0} )
                fr['relationStatus'] = fr['effect']
                del fr['effect']
                del fr['_id']

                if fr.has_key( 'backupFollowee' ):
                    del fr['backupFollowee']
                    fr['isUser'] = 0
                else:
                    del fr['followee']
                    fr['isUser'] = 1

                successInfo = deepcopy( ERR_SUCCESS )
                successInfo.message["data"] = fr
                self.write( json.dumps( successInfo.message, cls=MeEncoder ) )
            else:
                print "action error: " + action
                self.write( ERR_PATH_PERMISSION.message )
                return
        except Exception, e:
            log.err("FollowerHandler-->action:%s in post() error, %s", action, e)
            self.write(ERR_DB_OPERATION.message)
            return
        if action == 'follow':
            if is_user and not followed:
                try:
                    # 计数 newFans_ +1
                    ClassHelper('StatCount').updateOne({'name': 'newFans_' + followee},
                                                       {"$inc": {'count': 1}},
                                                       upsert=True)
                except Exception, e:
                    print e
                    self.write( ERR_DB_OPERATION.message )
                    return

                self.pushMessage( followee, userId )


    @tornado.web.asynchronous
    def pushMessage(self, followee, user):
        def callback(response):
            log.info( 'Push:%s', response.body)
            self.finish()

        pushUrl = BaseConfig.pushUrl
        pushData = {
            'userid': followee,
            'action': 'followed',
            'otherid': user
        }
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(pushUrl, callback=callback, method="POST", body=json.dumps(pushData), headers={'X-MeCloud-Debug': '1'})
