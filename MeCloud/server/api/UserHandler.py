# coding=utf8
import json
import tornado.web
from api.BaseHandler import BaseHandler
from helper.ClassHelper import ClassHelper
from helper.Util import MeEncoder, checkKeysAndValue, checkKeys
from lib import log
from model.MeError import *
from model.MeObject import MeObject
from model.MeQuery import MeQuery
from model.MeUser import MeUser


class UserHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        if self.user:
            del (self.user['password'])
            self.write(json.dumps(self.user, cls=MeEncoder))
        else:
            self.write(ERR_UNAUTHORIZED.message)

    def post(self, action=None):
        if action == 'signup':
            self.signup()
        elif action == 'login':
            self.login()
        elif action == 'modifyPwd':
            self.modifyPwd()
        elif action == 'update':
            pass
        # elif action=='loginWithoutPwd':
        #			self.loginWithoutPwd()
        else:
            log.err("userHandler path error %s", action)
            self.write(ERR_PATH_PERMISSION.message)

    @tornado.web.authenticated
    def put(self,action=None):
        if action == "update":
            try:
                obj = json.loads(self.request.body)
            except Exception, e:
                log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
                self.write(ERR_INVALID.message)
                return
            classHelper = ClassHelper("User")
            # 只返回了更新时间
            data = classHelper.update(self.user['_id'], obj)
            # 默认返回整个对象
            self.write(json.dumps(data, cls=MeEncoder))
        else:
            log.err("userHandler path error %s", action)
            self.write(ERR_PATH_PERMISSION.message)

    ### 注册接口
    def signup(self):
        obj = self.check_field("User",self.jsonBody)
        if not obj:
            return
        user = MeUser(obj)
        if user['username'] == None or user['password'] == None:
            self.write(ERR_PARA.message)
            return
        try:
            user.signup()
            del (user['password'])
            self.setUserCookie(user["_id"])
            self.write(json.dumps(user, cls=MeEncoder))
        except Exception, e:
            # TODO: 暂时只有重复
            self.write(ERR_PARA.message)

    ### 登录接口
    def login(self):
        user = MeUser(self.jsonBody)
        if user['username'] == None or user['password'] == None:
            self.write(ERR_PARA.message)

        if user.login(user['username'], user['password']):
            del (user['password'])
            self.write(json.dumps(user, cls=MeEncoder))
            self.set_secure_cookie("u", user['_id'])
            # userid = self.get_secure_cookie("u")
            # cookie = self.get_cookie("u")
            new_cookie= str(self._new_cookie.get('u')).split('=')[1].split(';')[0].replace('"', '')
            # new_cookie = str(self._new_cookie.get('u')).split('"')[1]
            print new_cookie
            print user['_id']
            if new_cookie is not None:
                self.set_user_cookie_record(new_cookie, user['_id'])
        else:
            self.write(ERR_USERPWD_MISMATCH.message)

    def loginWithoutPwd(self):
        obj = json.loads(self.request.body)
        if not checkKeys(obj, ['username']):
            self.write(ERR_PARA.message)
            return

        user = MeUser(self.appName, obj)
        userHelper = ClassHelper('develop', 'User')
        userInfo = userHelper.get(self.appInfo['user'])
        # library授权
        if userInfo['type'] == 2:
            if user['bundleId']:
                log.info("Library User[%s] Auth. bundleId[%s]", user['username'], user['bundleId']);
            elif user['package']:
                log.info("Library User[%s] Auth. package[%s]", user['username'], user['package']);
            log.info('auth app[%s]', self.appInfo['appName']);
        # 普通授权失败
        elif user['bundleId'] != None:
            if (not self.appInfo.has_key('bundleId')) or self.appInfo['bundleId'] != user['bundleId']:
                log.err('[%s] bundleId[%s] not match. LoginWithoutPwd Error.', self.appInfo['appName'],
                        user['bundleId'])
                self.write(ERR_UNAUTHORIZED.message)
                return
            log.info('auth app[%s]', self.appInfo['appName']);
        elif user['package']:
            if (not self.appInfo.has_key('package')) or self.appInfo['package'] != user['package']:
                log.err('[%s] package[%s] not match. LoginWithoutPwd Error.', self.appInfo['appName'], user['package'])
                self.write(ERR_UNAUTHORIZED.message)
                return
            log.info('auth app[%s]', self.appInfo['appName']);
        else:
            log.err("loginWithoutPwd Error: Invalid. %s", self.request.body)
            self.write(ERR_UNAUTHORIZED.message)
            return

        # 检查数量限制
        # userHelper = ClassHelper(self.appDb, "User")
        # userUpper = self.appInfo['userUpper']
        # # userUpper=0表示无数量限制
        # if userUpper>0:
        # 	if userHelper.count() > userUpper:
        # 		log.err('[%s] over user count limit', self.appInfo['appName']);
        # 		self.write(ERR_USER_PERMISSION.message)

        try:
            user.loginWithoutPwd()
            log.info('LoginWithoutPwd: %s', user['username'])
            self.set_secure_cookie("u", user['username'])
            user['authen'] = userInfo['authen'];
            self.write(json.dumps(user, cls=MeEncoder))

            # 登录日志
            loginLog = MeObject(self.appName, 'LoginLog')
            loginLog['username'] = user['username']
            if hasattr(self, 'client_ip'):
                loginLog['ip'] = self.client_ip;
            loginLog.save()
        except Exception, e:
            log.err("LoginWithoutPwd Error: %s Error:%s", self.request.body, str(e))
            self.write(str(e))

    def modifyPwd(self):
        obj = self.jsonBody
        if 'newPwd' not in obj:
            self.write(ERR_PARA.message)
        else:
            user = self.user
            if user == None:
                self.write(ERR_OBJECTID_MIS.message)
                return
            # if str(user['password']) == str(obj['oldPwd']):
            updateObj = {
                '$set': {
                    'password': obj['newPwd']
                }
            }
            userQuery = MeQuery("User")
            userQuery.update_core(user['_id'], updateObj)
            self.set_secure_cookie("u", user['_id'])
            self.write(ERR_SUCCESS.message)
            # else:
            #     self.write(ERR_PASSWD_INVALID.message)


    # def userRemark(self):
    #     try:
    #         obj = json.loads(self.request.body)
    #     except Exception, e:
    #         log.err("JSON Error:[%d/%s] , error:%s", len(self.request.body), self.request.body, str(e))
    #         self.write(ERR_INVALID.message)
    #         return
    #
    #     obj = self.check_field("UserRemark", obj)
    #     if not obj:
    #         return
    #     remarkObj = MeObject('UserRemark',obj)
    #     remarkQuery = MeQuery('UserRemark')
    #     if "remarker" in obj:
    #         item = remarkQuery.find_one({'user':self.user['_id'],"remarker":obj['remarker']})
    #         if not item:
    #             remarkObj['user'] = self.user['_id']
    #             remarkObj.save()
    #         else:
    #             for key,
