# coding=utf-8
from ConfigParser import ConfigParser

from application import Application

# from util.LoggerUtil import logger
from helper.ClassHelper import ClassHelper


class Application(Application):
    pass


if __name__ == '__main__':
    # logger.info('redis sub has run')
    Application().start()
    # logger.debug('server has run')

