# coding=utf8
import json

import copy
import tornado.web
from api.BaseHandler import BaseHandler
from helper.ClassHelper import ClassHelper
from helper.Util import MeEncoder
from lib import log
from model.MeError import *
from helper.CountHelper import *

import requests

sandboxUrl = "https://sandbox.itunes.apple.com/verifyReceipt"
buyUrl = "https://buy.itunes.apple.com/verifyReceipt"

class MyHandler(BaseHandler):
    @tornado.web.authenticated
    # def get(self, objectId, action, isUser=1):
    def get(self, action):
        if action == "albumUser":#弃用，用下面的那个
            classHelper = ClassHelper("Face")
            result = classHelper.find({"$and":[{'createAt': {'$gt': '2017-09-20 00:00:00'}},{'createAt': {'$lt': '2017-10-01 00:00:00'}}]})
            print "++++++++++++++++++++++++"
            for res in result:
                print 'test',res
                break
        elif action == "albumUserTwo":
            classHelper = ClassHelper('Media')
            items = classHelper.aggregate(
                                [
                                    {
                                        # '$match': {'uploader': "59dc3decca7143413c03a62f", 'publish': False}
                                        '$match': {'uploader': self.user['_id'], 'publish': False}
                                    },
                                    {
                                        '$project': {'faces': 1}
                                    },
                                    {
                                        '$unwind': "$faces"
                                    },
                                    {
                                        "$lookup": {
                                            "from": "Face",
                                            "localField": "faces",
                                            "foreignField": "_sid",
                                            "as": "faceInfo"
                                        }
                                    },
                                    {
                                        '$unwind': "$faceInfo"
                                    },
                                    {
                                        "$project": {"faces": 1, "possible": "$faceInfo.possible", 'media': "$faceInfo.media"}
                                    },
                                    {
                                        "$unwind": "$possible"
                                    },
                                    {
                                        '$group': {
                                            "_id": {'userId': "$possible.user", "backupUserId": "$possible.backupUser"},
                                            "media": {'$first': "$media"},
                                            "count": {'$sum': 1}
                                        }
                                    },
                                    {"$sort": {"count": -1}},
                                    {
                                        '$lookup': {
                                            "from": "UserInfo",
                                            "localField": "_id.userId",
                                            "foreignField": "user",
                                            "as": "userInfo"
                                        }
                                    },
                                    {
                                        '$lookup': {
                                            "from": "BackupUser",
                                            "localField": "_id.backupUserId",
                                            "foreignField": "_sid",
                                            "as": "backupUserInfo"
                                        }
                                    }
                                ]
            )
            userInfo = []
            for obj in items:
                try:
                    if obj['userInfo']:
                        userInfo.append({'nickName':obj['userInfo'][0].get('nickName',None),'userId':obj["_id"]['userId'],'count':obj['count']})
                    else:
                        userInfo.append({'nickName': obj['backupUserInfo'][0].get('nickName', None), 'backupUserId': obj["_id"]['backupUserId'],'count':obj['count']})
                except Exception,e:
                    log.err("MyHandler-->get user(backup) info err for userId:%s", obj['_id'])
            data = copy.deepcopy(ERR_SUCCESS)
            data.message['data'] = userInfo
            self.write(json.dumps(data.message, cls=MeEncoder))
        elif action == "share":
            if self.request.arguments.has_key('platform') and self.request.arguments.has_key('type'):
                #where={'platform':"","type":""}
                query = {
                    "platform": self.get_argument('platform'),
                    "type": self.get_argument('type')
                }
                # query['type'] = "app"
                classHelper = ClassHelper("ShareCopywrite")
                objs = classHelper.find_one(query)

                if objs['type'] == "app":#分享app
                    objs = self.filter_field(objs)
                    if "file" in objs:
                        objs['imageUrl'] = self.getFile(objs['file'])
                else:#分享user或者backupUser或者分享图片
                    if objs['type'] == "image":  # 分享图片
                        if self.request.arguments.has_key('userId'):
                            item = self.getUser(self.get_argument("userId"))
                        else:
                            item = {}
                    else:#分享user或者backupUser
                        if not self.request.arguments.has_key('userId'):
                            self.write(ERR_PATH_PERMISSION.message)
                            return
                        isUser = 1
                        if objs['type'] == "backupUser":
                            isUser = 0
                        userId = self.get_argument("userId")
                        item = self.getCountUser(userId, isUser)
                        objs['url'] = objs['url'] + "?userId=" + userId + "&isUser=" + str(isUser)
                    if item:
                        try:
                            item['nickName'] = item['nickname']
                        except:
                            pass
                        try:
                            objs['title'] = objs['title'].format(**item)
                        except:
                            objs.pop("title", None)
                        try:
                            objs['subTitle'] = objs['subTitle'].format(**item)
                        except:
                            objs.pop("subTitle", None)
                        if objs.get('file', None) == "{avatar}":
                            objs['imageUrl'] = self.getFile(item['avatar'])
                    else:
                        objs.pop("title",None)
                        objs.pop("subTitle",None)
                objs = self.filterField(objs)
                self.write(json.dumps(objs, cls=MeEncoder))
            else:
                self.write(ERR_PATH_PERMISSION.message)
        elif action == "appleRec":
            classHelper = ClassHelper("RechargeFlow")
            obj = classHelper.get("59fc415bd234013c71ad25b6")
            data = {
                "receipt-data":obj['order']['certificate']
            }
            result = self.appleVerify(buyUrl, sandboxUrl, data, 1)
            self.write(result)
        elif action == "info":
            # userId = "5a0188ccca714319e603c9e8"
            result = self.userCountTwo(objectId,int(isUser))
            self.write(json.dumps(result))

        elif action == "qrcode":
            if not self.request.arguments.has_key('shareTargetId') or not self.request.arguments.has_key('shareType'):
                self.write(ERR_PATH_PERMISSION.message)
                return
            shareType = int(self.get_argument("shareType"))
            shareTargetId = self.get_argument("shareTargetId")
            # 记录图片分享
            try:
                shareRecordHelper = ClassHelper("ShareRecords")
                shareInfo = shareRecordHelper.create({
                    "from": self.user['_id'],
                    "shareTargetId": shareTargetId,
                    "type": shareType,
                    "compareFaceId": self.get_argument("compareFaceId")
                })
                url = "http://heyhoney.blinnnk.com/" + "?compareId=" + shareInfo['_id']
                self.write(json.dumps({"url":url}))
            except:
                self.write(ERR_PATH_PERMISSION.message)

        elif action == "sharerecord":
            if not self.request.arguments.has_key('compareId'):
                self.write(ERR_PATH_PERMISSION.message)
                return
            compareId = self.get_argument("compareId")
            shareRecordHelper = ClassHelper("ShareRecords")
            srItem = shareRecordHelper.get(compareId)
            if srItem:
                srItem = self.filter_field(srItem)
                result = {}
                if srItem['shareType'] < 2:
                    item = self.getUser(srItem['shareTargetId'], srItem['shareType'])
                    if item:
                        result['nickname'] = item['nickName']
                        result['avatar'] = item['avatar']
                        if "user" in item:
                            result['userId'] = item['user']
                        else:
                            result['userId'] = item['_id']
                        result.update(srItem)
                else:
                    result = self.getFace(srItem['shareTargetId'])

                self.write(json.dumps(result, cls=MeEncoder))
            else:
                self.write(ERR_PATH_PERMISSION.message)

        elif action == "deleteMediaFace":
            if not self.request.arguments.has_key('mediaId'):
                self.write(ERR_PATH_PERMISSION.message)
                return
            mediaId = self.get_argument("mediaId")
            result = self.deleteMediaFace(mediaId)



        else:
            self.write(ERR_UNAUTHORIZED.message)

    def userCount(self, userId, isUser=1):#isUser：1真实用户，0backupUser
        obj = {
            'followeesCount': 0,
            'followeeStatus': 0,
            'blackStatus': 0,
            'isUser':isUser #1为user，0为backupUser
        }
        try:
            classHelper = ClassHelper('StatCount')
            if isUser:
                userInfoHelper = ClassHelper('UserInfo')
                item = userInfoHelper.find_one({"user": userId})
                obj['user'] = item['user']
                # obj["nickName"] = item.get("nickName",None)
                # obj["avatar"] = item.get("avatar", None)
                # 关注数
                followeesCount = classHelper.find_one({'name': "followees_" + userId}) or {}
                obj['followeesCount'] = followeesCount.get('count', 0)
            else:
                backupUserHelper = ClassHelper('BackupUser')
                item = backupUserHelper.find_one({"_id": userId})
                obj['user'] = item['_id']

            if item:
                obj["nickName"] = item.get("nickName", None)
                obj["avatar"] = item.get("avatar", None)
                obj["age"] = item.get("age",0)
                obj["address"] = item.get("address",None)
                obj['rect'] = item.get("rect",None)
                obj["_id"] = item['_id']
            #粉丝数
            followersCount = classHelper.find_one({'name': "followers_" + userId}) or {}
            obj['followersCount'] = followersCount.get('count', 0)
            #贡献者数
            assignersCount = classHelper.find_one({'name': "assigners_" + userId}) or {}
            obj['assignersCount'] = assignersCount.get('count', 0)
            #照片数
            mediasCount = classHelper.find_one({'name': "medias_" + userId}) or {}
            obj['mediasCount'] = mediasCount.get('count', 0)
            if self.user["_id"] != userId:
                #关注状态
                followHelper = ClassHelper('Followee')
                item = followHelper.find_one({"user":self.user['_id'],"followee":userId, "effect":{"$gt":0}})
                if item:#0 没有关系 1 关注 2 相互关注 3 粉丝关系
                    obj['followeeStatus'] = item['effect']
                else:
                    item = followHelper.find_one({"followee": self.user['_id'], "user": userId})
                    if item:
                        obj['followeeStatus'] = 3
                #拉黑状态
                blackHelper = ClassHelper('Blacklist')
                item = blackHelper.find_one({"user": self.user['_id'], "blacker": userId, "effect":{"$gt":0}})
                if item:
                    obj['blackStatus'] = 1
        except Exception,ex:
            log.err(ex.message)
            return ERR_INVALID.message
        return obj

    def userCountTwo(self, userId, isUser=1):#isUser：1真实用户，0backupUser
        obj = {
            'followeesCount': 0,
            'followeeStatus': 0,
            'blackStatus': 0,
            'isUser':isUser #1为user，0为backupUser
        }
        try:
            followeeHelper = ClassHelper('Followee')
            faceHelper = ClassHelper('Face')
            if isUser:
                userInfoHelper = ClassHelper('UserInfo')
                item = userInfoHelper.find_one({"user": userId})
                obj['user'] = item['user']
                # obj["nickName"] = item.get("nickName",None)
                # obj["avatar"] = item.get("avatar", None)
                # 关注数
                followeesCount = followeeHelper.query_count({'user':userId,"effect":{"$gt":0}}) or 0
                obj['followeesCount'] = followeesCount
            else:
                backupUserHelper = ClassHelper('BackupUser')
                item = backupUserHelper.find_one({"_id": userId})
                obj['user'] = item['_id']

            if item:
                obj["nickName"] = item.get("nickName", None)
                obj["avatar"] = item.get("avatar", None)
                obj["age"] = item.get("age",0)
                obj["address"] = item.get("address",None)
                obj['rect'] = item.get("rect",None)
                obj["_id"] = item['_id']
            #粉丝数
            followersCount = followeeHelper.query_count({'followee':userId,"effect":{"$gt":0}}) or 0
            obj['followersCount'] = followersCount
            #贡献者数
            assignersCount = faceHelper.distinct({'assign.user':userId},"assign.assigner") or []
            obj['assignersCount'] = len(assignersCount.cursor)
            #照片数
            mediasCount = faceHelper.query_count({'assign.user':userId}) or 0
            obj['mediasCount'] = mediasCount
            if self.user["_id"] != userId:
                #关注状态

                item = followeeHelper.find_one({"user":self.user['_id'],"followee":userId, "effect":{"$gt":0}})
                if item:#0 没有关系 1 关注 2 相互关注 3 粉丝关系
                    obj['followeeStatus'] = item['effect']
                else:
                    item = followeeHelper.find_one({"followee": self.user['_id'], "user": userId})
                    if item:
                        obj['followeeStatus'] = 3
                #拉黑状态
                blackHelper = ClassHelper('Blacklist')
                item = blackHelper.find_one({"user": self.user['_id'], "blacker": userId, "effect":{"$gt":0}})
                if item:
                    obj['blackStatus'] = 1
        except Exception,ex:
            log.err(ex.message)
            return ERR_INVALID.message
        return obj

    def getFile(self,fileId):
        fileHelper = ClassHelper('File')
        obj = fileHelper.get(fileId)
        # fileUrl = "http://"+obj['bucket']+".oss-cn-beijing.aliyuncs.com/"+obj['name']
        fileUrl = "http://" + self.request.host + "/1.0/file/download/"+obj['_id']
        return fileUrl
    def getUser(self, userId, isUser=-1):
        if isUser == 1:
            userHelper = ClassHelper("UserInfo")
            obj = userHelper.find_one({'user': userId}) or {}
        else:
            obj = ClassHelper("BackupUser").get(userId) or {}
        if not obj:
            userHelper = ClassHelper("UserInfo")
            obj = userHelper.find_one({'user':userId}) or {}
        return self.filter_field(obj)

    def getFace(self, faceId):
        faceHelper = ClassHelper("Face")
        obj = faceHelper.find_one(query={"_id": faceId}, keys={"rect": 1, "possible.score": 1, "file": 1}) or {}
        item = {}
        item['faceId'] = faceId
        item['rect'] = obj['rect']
        item['file'] = obj['file']
        item['score'] = obj['possible'][0]['score']
        # user = {}
        # if obj:
        #     if "uploader" in obj:
        #         user = self.getUser(obj['uploader'],1)
        #     elif "backupUser" in obj:
        #         user = self.getUser(obj['backupUser'], 0)
        #     else:
        #         pass
        #     user = self.filter_field(user)
        # obj = self.filter_field(obj)
        return item

    def getCountUser(self, userId, isUser=1):
        item = profile(userId, isUser)
        obj = copy.deepcopy(item)
        item['assignersCount'] = item.get('assigners',0)
        item['followersCount'] = item.get('followers',0)
        item['imageCount'] = item.get('medias',0)
        faceHelper = ClassHelper('Face')
        toClaimCount = faceHelper.query_count({'assign.user': userId, 'assign.status': 0}) or 0
        item['toClaimCount'] = toClaimCount
        if item['assignersCount'] and item['followersCount'] and item['imageCount'] and item['toClaimCount']:
            return item
        return obj

    def filterField(self, obj):
        obj = self.filter_field(obj)
        obj.pop("file",None)
        obj.pop("platform", None)
        return obj

    def deleteMediaFace(self, mediaId):
        mediaHelper = ClassHelper("Media")
        media = mediaHelper.find_one(query={"_id":mediaId}, keys={"faces":1})
        tran = []
        if media:
            for face in media['faces']:
                tran.append({
                    'destClass': 'Face',
                    'query': {'_id': face},
                    'action': {'@set': {'status': 0}}
                })
            result = mediaHelper.update(mediaId,{"$set":{'status':0}},transaction=tran)
            if result:
                self.write(ERR_SUCCESS.message)
            else:
                self.write(ERR_INVALID.message)
        else:
            self.write(ERR_PATH_PERMISSION.message)

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
        else:  #无数据返回
            if count == 3:#三次验证
                return result
            else:
                count = count + 1
                return self.appleVerify(url, testUrl, data, count)


