package com.rex.mecloud;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Created by Visionin on 17/7/18.
 */

public class MeCloud extends Handler{
    protected static volatile MeCloud mInstance = null;

    /**
     * 单例
     * @return
     */
    public static MeCloud shareInstance(){
        if (mInstance == null) {
            synchronized (MeCloud.class) {
                if (mInstance == null) {
                    mInstance = new MeCloud();
                }
            }
        }
        return mInstance;
    }

    private MeCloud(){
        super(Looper.getMainLooper());
    }

    public native static void initialize(String appId, String appKey);
}
