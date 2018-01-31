# -*- coding: utf-8 -*-
import urllib2

import oss2
import tornado.web
from bson import ObjectId

from api.BaseHandler import BaseHandler
from lib import crypto,log
from model.MeError import ERR_OBJECTID_MIS
from model.MeFile import MeFileConfig
from model.MeQuery import MeQuery


class FileDownloadHandler(BaseHandler):

    isImage = False
    def get(self, objectId):
        try:
            ObjectId(objectId)
        except Exception:
            return self.write(ERR_OBJECTID_MIS.message)
        fileQuery = MeQuery("File")
        # log.info("Download objectId one: %s",objectId)
        file = fileQuery.get(objectId)
        if file == None:
            self.write(ERR_OBJECTID_MIS.message)
        else:
            self.isImage = True
            self.getImage(file)

    def getImage(self, file):
        # # log.info("Download objectId: %s",file['_id'])
        # try:
        #     url = "http://" + file['bucket'] + ".oss-" + MeFileConfig.region_id + "-internal.aliyuncs.com/" + file["name"]
        # except:
        #     url = "http://" + MeFileConfig.bucket_name + ".oss-" + MeFileConfig.region_id + "-internal.aliyuncs.com/" + file['_id']
        #
        process = None
        if self.request.arguments.has_key('x-oss-process'):
            process = self.get_argument("x-oss-process")
        # log.info("Download url: %s", url)
        # response = urllib2.urlopen(url)
        # self.isImage = True
        # # with open("test.jpg","w") as text:
        # #     text.write(response.read())
        # self.write(response.read())
        auth = oss2.Auth("LTAIkQ8yPr2iNv7e", "DYGeKLDb079W9i0i0bjw458BEJaN5C")
        bucket = oss2.Bucket(auth, "oss-" + MeFileConfig.region_id + ".aliyuncs.com", file['bucket'])
        result = bucket.get_object(file["name"],process=process)
        data = result.read()
        # with open("test.jpg", "wb") as code:
        #     code.write(data)
        self.write(data)



    def write(self, msg):
        if not self.isImage:
            BaseHandler.write(self, msg)
        else:
            tornado.web.RequestHandler.write(self, str(crypto.imageEncrypt(msg)))
