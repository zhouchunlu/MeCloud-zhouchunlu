# coding=utf-8
import threading
from ConfigParser import ConfigParser

from mecloud.application import Application
from mecloud.helper.RedisHelper import RedisDBConfig

from es import EsClient
from processor import RedisThread, PingThread
from util.LoggerUtil import logger
from ws import Constants


class Application(Application):
    pass


threads = []
t1 = threading.Thread(target=RedisThread.sub_pub_start)
# t2 = threading.Thread(target=PingThread.check)
threads.append(t1)
# threads.append(t2)

if __name__ == '__main__':
    config = ConfigParser()
    config.read('./config')
    mode = config.get('global', 'mode')
    # set redis config and create redis pool
    RedisDBConfig.HOST = config.get('redis', 'REDIS_HOST')
    RedisDBConfig.PASSWORD = config.get('redis', 'REDIS_PASSWORD')
    Constants.REDIS_CHANNEL_FOR_PUSH = config.get('redis', 'REDIS_SUB_CHANNEL')
    EsClient.ES_SERVERS = [{
        'host': config.get('es', 'ES_HOST'),
        'port': config.get('es', 'ES_PORT')
    }]
    EsClient.init()
    for t in threads:
        t.setDaemon(True)
        t.start()
    logger.info('redis sub has run')
    Application().start()
    logger.debug('server has run')
