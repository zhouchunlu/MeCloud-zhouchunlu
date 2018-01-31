# -*- coding: utf-8 -*-
'''
 * file :	crypto.py
 * author :	Rex
 * create :	2017-08-15 13:46
 * func : 
 * history:
'''
from ctypes import *

from os.path import abspath, dirname,os,sys

# module = cdll.LoadLibrary(dirname(abspath(__file__))+"/crypto_string.so")


def encrypt(en_str):
    return en_str


### 解密
def decrypt(de_str):
    return de_str


# 图片加密
def imageEncrypt(en_str):
    imageBytes = bytearray(en_str)
    outByteArray = bytearray()
    j = 0
    for i in range(len(imageBytes)):
        temp = None
        # print imageBytes[i]
        j = j + 1
        if j > 255:
            j = 0

        if imageBytes[i] + (j / 5 + j % 3) > 255:
            temp = imageBytes[i] + (j / 5 + j % 3) - 256
        else:
            temp = imageBytes[i] + (j / 5 + j % 3)
        outByteArray.append(temp)
    return outByteArray

# 图片解密
def imageDecrypt(en_str):
    imageBytes = bytearray(en_str)
    outByteArray = bytearray()
    j = 0
    for i in range(len(imageBytes)):
        temp = None
        j = j + 1
        if j > 255:
            j = 0
        if imageBytes[i] - (j / 5 + j % 3) < 0:
            temp = 256 + imageBytes[i] - (j / 5 + j % 3)
        else:
            temp = imageBytes[i] - (j / 5 + j % 3)
        outByteArray.append(temp)
    return outByteArray
