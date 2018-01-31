# -*- coding: utf-8 -*-
import json
import tornado.web
from api.BaseHandler import BaseHandler
from helper.Util import MeEncoder
from model.MeError import ERR_PARA, ERR_INVALID
from model.MeFile import MeFile
from model.MeFile import MeFileConfig


class FileHandler(BaseHandler):

    isImaget = False

    @tornado.web.authenticated
    def get(self, action=None):
        if action == 'token':
            file = MeFile()
            token = file.fetch_sts_token()
            self.write(json.dumps(token, cls=MeEncoder))
        else:
            self.write(ERR_PARA.message)


                # if self.request.arguments.has_key('object_id'):
                #     objectId = self.get_argument('object_id')
                #     try:
                #         ObjectId(objectId)
                #     except Exception:
                #         return self.write(ERR_PARA.message)
                #     fileQuery = MeQuery("File")
                #     file = fileQuery.get(objectId)
                #     if file == None:
                #         self.write(ERR_OBJECTID_MIS.message)
                #     self.write(json.dumps(file, cls=MeEncoder))
                # else:
                #     return self.write(ERR_PARA.message)

    @tornado.web.authenticated
    def post(self, action=None):
        if action == 'upload':
            self.upload()
        elif action == 'uploadFile':
            self.uploadFile()
        elif action == 'putFile':
            self.putFile()
        else:
            return self.write(ERR_PARA.message)

    def upload(self):
        if not self.jsonBody.has_key('name'):
            self.write(ERR_PARA.message)
            return
        # data = None
        # if "data" in self.jsonBody:
        #     data = self.jsonBody.pop("data", None)
        obj = self.check_field("File",self.jsonBody)
        if not obj:
            return
        file = MeFile(obj)
        if file['name'] == None:
            self.write(ERR_PARA.message)
            return
        try:
            file.upload()
            self.write(json.dumps(file, cls=MeEncoder))

        except Exception, e:
            print e
            self.write(ERR_INVALID.message)


    def uploadFile(self):
        # if not self.jsonBody.has_key('data'):
        #     self.write(ERR_PARA.message)
        # data = None
        # if "data" in self.jsonBody:
        #     data = self.jsonBody.pop("data", None)
        obj = self.check_field("File", self.jsonBody)
        if not obj:
            return
        file = MeFile(obj)
        file['bucket'] = MeFileConfig.bucket_name
        file['platform'] = MeFileConfig.platform
        file.save()
        if file:
            name = file['_id']
            file['name'] = name
            file.save()
            file = self.filter_field(file)
            # file.upload_data(file['name'],data)
            self.write(json.dumps(file, cls=MeEncoder))
    def putFile(self, name, data):
        file = MeFile()
        file.upload_data(name,data)
