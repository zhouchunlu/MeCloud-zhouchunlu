# -*- coding: utf-8 -*-

import json
import re

import bson
import copy
import requests
import tornado.web
import tornado.gen
from api.BaseHandler import BaseHandler, BaseConfig
from bson import ObjectId
from helper.ClassHelper import ClassHelper
from helper.SensitiveHelper import SensitiveHelper
from helper.Util import MeEncoder
from lib import log
from model.MeACL import MeACL
from model.MeError import *
from model.MeObject import MeObject
from helper.BlacklistHelper import BlacklistHelper
from helper.PushHelper import PushHelper


class ClassHandler(BaseHandler):
    ### 获取对象 及 批量查询
    # @tornado.web.authenticated
    def get(self, className, objectId=None):
        admin = False
        if self.get_current_user() in BaseConfig.adminUser:
            admin = True
        if not admin:
            if className in BaseConfig.accessNoClass:
                self.write(ERR_CLASS_PERMISSION.message)
                return
            if className not in BaseConfig.projectClass:
                #不存在的class
                self.write(ERR_PATH_PERMISSION.message)
                return
        verify = self.verify_cookie(className)
        if not verify:
            self.write(ERR_UNAUTHORIZED.message)
            return
        if objectId:
            try:
                ObjectId(objectId)
            except Exception:
                self.write(ERR_OBJECTID_MIS.message)
                return
            obj = MeObject(className)
            if not obj.get(objectId):
                self.write(ERR_OBJECTID_MIS.message)
            else:
                mo = obj.get(objectId)
                self.filter_field(mo)
                self.write(json.dumps(mo, cls=MeEncoder))
        else:
            classHelper = ClassHelper(className)
            query = {}
            objs = None
            if self.request.arguments.has_key('aggregate'):
                query = eval(self.get_argument('aggregate'))
                objs = classHelper.aggregate(query)
            else:
                if self.request.arguments.has_key('where'):
                    query = eval(self.get_argument('where'))
                    try:
                        if query.has_key('_id'):
                            ObjectId(query['_id'])
                        if query.has_key('$or'):
                            for item in query['$or']:
                                if "_id" in item:
                                    item["_id"] = ObjectId(item["_id"])
                    except Exception:
                        self.write(ERR_OBJECTID_MIS.message)
                        return
                if self.request.arguments.has_key('keys'):
                    keys = eval(self.get_argument('keys'))
                else:
                    keys = None

                try:
                    sort = json.loads(self.get_argument('sort','{}'))
                    idSort = sort.get('_id', -1)
                    sort = sort or None

                except Exception, e:
                    self.write(ERR_INVALID.message)
                    print e
                    return

                try:
                    if self.request.arguments.has_key('startId'):
                        startId = self.get_argument('startId')
                        if idSort == -1:
                            query["_id"] = {"$lt": ObjectId(startId)}
                        elif idSort == 1:
                            query["_id"] = {"$gt": ObjectId(startId)}
                    if self.request.arguments.has_key('limit'):
                        limit = int(self.get_argument('limit'))
                    else:
                        limit = 20
                except Exception:
                    self.write(ERR_INVALID.message)
                    return

                skip = 0
                try:
                    if self.request.arguments.has_key('skip'):
                        skip = int(self.get_argument('skip'))
                except Exception:
                    self.write(ERR_INVALID.message)
                    return


                if limit > 100:
                    self.write(ERR_INVALID.message)
                    return

                objs = classHelper.find(query, keys, sort, limit, skip)

            objects = []
            for obj in objs:
                mo = MeObject(className, obj, False)
                mo.overLoadGet = False
                if self.get_current_user() and not admin:
                    acl = MeACL(mo['acl'])
                    if not acl.readAccess(self.user):
                        continue
                self.filter_field(mo)
                objects.append(mo)
            self.write(json.dumps(objects, cls=MeEncoder));

    ### 创建对象, 返回ObjectId, createAt, updateAt
    @tornado.web.authenticated
    def post(self, className):
        # try:
            try:
                obj = json.loads(self.request.body)
                obj = self.check_field(className, obj)
                if not obj:
                    return
            except Exception, e:
                log.err("JSON Error:%s , error:%s", self.request.body, str(e))
                self.write(ERR_INVALID.message)
                return
            print 'className:' + className
            if type(obj) == list:
                objectIdError = False
                for index in range(len(obj) - 1):
                    try:
                        for key, value in obj[index].items():
                            if value.has_key('_sid'):
                                ObjectId(value['_sid'])
                            value = self.sentiveCheck(key, value)
                            value = self.blacklistCheck(className, value)
                            if value:
                                meobj = MeObject(key, value)
                                meobj.save()
                            else:
                                self.write(ERR_BLACK_PERMISSION.message)
                    except bson.errors.InvalidId:
                        objectIdError = True
                        break
                    except Exception, e:
                        log.err("Error:%s , error:%s", self.request.body, str(e))
                if objectIdError:
                    self.write(ERR_OBJECTID_MIS.message)
                    return
                mainObj = obj[len(obj) - 1]
                try:
                    if mainObj.has_key('_sid'):
                        ObjectId(mainObj['_sid'])
                    mainObj = self.sentiveCheck(className, mainObj)
                    mainObj = self.blacklistCheck(className, mainObj)
                    if mainObj:
                        meobj = MeObject(className, mainObj)
                        meobj.save()
                        self.write(json.dumps(meobj, cls=MeEncoder))
                        self.finish()
                        self.pushMessage(className, meobj)

                    else:
                        self.write(ERR_BLACK_PERMISSION.message)
                except bson.errors.InvalidId:
                    self.write(ERR_OBJECTID_MIS.message)
            else:
                try:
                    obj = self.sentiveCheck(className, obj)
                    obj = self.blacklistCheck(className, obj)
                    if obj:
                        meobj = MeObject(className, obj)
                        meobj.save()
                        self.filter_field(meobj)
                        self.write(json.dumps(meobj, cls=MeEncoder))
                        self.finish()
                        # self.pushMessage(className, meobj)
                    else:
                        self.write(ERR_BLACK_PERMISSION.message)
                except Exception,e:
                    log.err(json.dumps(e.message))
                    if isinstance(e.message,dict) and e.message["errCode"] == 137:
                        field = re.search(r"index: ([0-9a-zA-Z]+)_-?\d{1} dup key",e.message['info'])
                        if field:
                            field = field.group(1)
                            classHelper = ClassHelper(className)
                            item = classHelper.find_one({field:obj[field]})
                            item = self.filter_field(item)
                            e.message['data'] = item
                    self.write(e.message)
        # except Exception, e:
        #     log.err("ClassHandler-->put error, %s", e)
        #     self.write(ERR_DB_OPERATION.message)

    ### 更新对象
    @tornado.web.authenticated
    def put(self, className, objectId=None):
        if not objectId and not self.request.arguments.has_key('where'):
            self.write(ERR_OBJECTID_MIS.message)
            return
        try:
            if objectId:
                try:
                    ObjectId(objectId)
                except Exception:
                    self.write(ERR_OBJECTID_MIS.message)
                    return
            obj = json.loads(self.request.body)
        except Exception, e:
            log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
            self.write(ERR_INVALID.message)
            return
        if self.request.arguments.has_key('where'):
            classHelper = ClassHelper(className)
            query = eval(self.get_argument('where'))
            obj = self.check_field(className, obj)
            if not obj:
                return
            upsert = eval(self.get_argument('upsert',"False"))
            returnObj = classHelper.updateOneCreate(query, obj)
            data = copy.deepcopy(ERR_SUCCESS)
            data.message['data'] = self.filter_field(returnObj)
            self.write(json.dumps(data.message ,cls=MeEncoder))
        elif type(obj) == list:
            objectIdError = False
            for index in range(len(obj) - 1):
                try:
                    for key, value in obj[index].items():
                        if value.has_key('_sid'):
                            ObjectId(value['_sid'])
                        value = self.sentiveCheck(key, value)
                        meobj = MeObject(key, value)
                        meobj.save()
                except bson.errors.InvalidId:
                    objectIdError = True
                    break
                except Exception, e:
                    log.err("Error:%s , error:%s", self.request.body, str(e))
            if objectIdError:
                self.write(ERR_OBJECTID_MIS.message)
                return
            mainObj = obj[len(obj) - 1]
            mainObj = self.sentiveCheck(className, mainObj)
            classHelper = ClassHelper(className)
            # 只返回了更新时间
            data = classHelper.update(objectId, mainObj)
            # 默认返回整个对象
            self.write(json.dumps(data, cls=MeEncoder))
        else:
            classHelper = ClassHelper(className)
            item = classHelper.get(objectId)#权限判断
            if not item:
                log.err("%s not exists",objectId)
                self.write(ERR_NOTFOUND.message)
                return
            if "acl" in item:
                acl = MeACL(item['acl'])
                if not acl.writeAccess(self.user):
                    self.write(ERR_CLASS_PERMISSION.message)
                    return
            else:
                self.write(ERR_CLASS_PERMISSION.message)
                return
            obj = self.sentiveCheck(className, obj)
            # 只返回了更新时间
            data = classHelper.update(objectId, obj)
            # 默认返回整个对象
            self.filter_field(data)
            self.write(json.dumps(data, cls=MeEncoder))

    ### 删除对象
    @tornado.web.authenticated
    def delete(self, className, objectId):
        if not objectId:
            self.write(ERR_PARA.message)
            return
        if BaseConfig.deleteClass.count(className) <= 0:
            self.write(ERR_USER_PERMISSION.message)
            return
        try:
            ObjectId(objectId)
        except Exception:
            self.write(ERR_OBJECTID_MIS.message)
            return
        classHelper = ClassHelper(className)
        obj = classHelper.find_one({"_id": objectId})
        if not obj:
            self.write(ERR_OBJECTID_MIS.message)
            return
        mo = MeObject(className, obj, False)
        mo.overLoadGet = False
        acl = MeACL(mo['acl'])
        if not acl.deleteAccess(self.user):
            self.write(ERR_USER_PERMISSION.message)
            return
        else:
            classHelper.delete(objectId)
            self.write(ERR_SUCCESS.message)

    def sentiveCheck(self,className,obj):
        if className in ["Comment", "Message", "UserInfo", "BackupUser", "UserRemark"] and self.get_current_user() not in BaseConfig.adminUser:
            for key in obj:
                if isinstance(obj[key],dict):
                    obj[key] = self.sentiveCheck(className,obj[key])
                elif isinstance(obj[key],unicode):
                    if key in ["content","nickName"]:
                        sensitiveHelper = SensitiveHelper(obj[key])
                        obj[key] = sensitiveHelper.filterWord(str(self.user["_id"]))
        return obj

    def blacklistCheck(self, className, obj):
        blacklistHelper = BlacklistHelper(className)
        item = blacklistHelper.filterAuTH(self.user["_id"], obj)
        if item:
            return item

    @tornado.web.asynchronous
    @tornado.gen.engine
    def pushMessage(self, className, obj):
        pushUrl = BaseConfig.pushUrl
        if className == "Followee" and self.request.method.upper() == "POST":
            ##粉丝推送
            pushData = {
                'userid':obj['followee'],
                'action':'followed',
                'otherid':self.user['_id']
            }
            requests.post(pushUrl, data=json.dumps(pushData), headers={'X-MeCloud-Debug': '1'})

