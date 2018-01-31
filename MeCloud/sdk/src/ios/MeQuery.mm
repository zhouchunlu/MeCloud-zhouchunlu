//
//  MeQuery.m
//  MeCloud
//
//  Created by super on 2017/7/20.
//  Copyright © 2017年 Rex. All rights reserved.
//

#include "MeQuery.h"
#include "MeIOSCallback.h"

void MeQuery::find(MeCallbackBlock block){
    ReferenceCache* cache = ReferenceCache::shareInstance();
    MeBlockCallback* callback = (MeBlockCallback*)cache->get();
    if (callback==NULL) {
        callback = new MeBlockCallback(m_classname);
        cache->add(callback);
    }
    callback->setBlock(block);
    
    MeQuery::find(callback);
}
