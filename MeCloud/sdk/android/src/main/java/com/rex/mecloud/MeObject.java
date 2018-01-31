package com.rex.mecloud;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.os.Parcel;
import android.os.Parcelable;
import android.util.Log;

import com.rex.load.NativeLoad;
import com.rex.utils.SignedUtil;

import static com.rex.load.NativeLoad.registJNIMethod;
import static com.rex.utils.SignedUtil.*;

/**
 * Created by Visionin on 17/7/18.
 */

public class MeObject implements Parcelable {
    public long             objectPtr   =0;
    protected String        className   = null;

    public MeObject(){}

    public MeObject(String className){
        this.className = className;
        objectPtr = create(className);
        Log.e("obj", "ptr: "+objectPtr);
    }

    protected MeObject(Parcel in) {
        objectPtr = in.readLong();
        className = in.readString();
    }

    /**
     * 深拷贝
     * @param copy
     * @return
     */
    public static MeObject deepCopy(MeObject copy){
        MeObject obj = new MeObject(copy.className);
        //TODO copy的objectPtr指向的jni层MeObject深拷贝到obj中

        return obj;
    }

    @Override
    protected void finalize() throws Throwable {
        super.finalize();
        destroy();
    }

    public  <T> void put(String key, T value){
        if (value instanceof String){
            putString(key, (String)value);
        } else if (value instanceof Double){
            putDouble(key, ((Double) value).doubleValue());
        } else if (value instanceof Integer){
            putInt(key, ((Integer) value).intValue());
        } else if (value instanceof Long){
            putLong(key, ((Long) value).longValue());
        } else if (value instanceof Float){
            putFloat(key, ((Float) value).floatValue());
        } else if (value instanceof Boolean){
            putBoolean(key, ((Boolean) value).booleanValue());
        }
    }

    /**
     * 异步save回调接口， jni中调用
     * @param callback
     */
    public void callback(final MeCallback callback, final MeException err){
        MeCloud.shareInstance().post(new Runnable() {
            @Override
            public void run() {
                callback.done(MeObject.this, err);
            }
        });
    }

    public native long create(String className);
    public native void save(MeCallback callback);
    protected native void destroy();
    public native String objectId();

    public native void putString(String key, String value);
    public native void putDouble(String key, double value);
    public native void putInt(String key, int value);
    public native void putLong(String key, long value);
    public native void putFloat(String key, float value);
    public native void putBoolean(String key, boolean value);

    public native String stringValue(String key);
    public native double doubleValue(String key);
    public native int intValue(String key);
    public native long longValue(String key);
    public native float floatValue(String key);
    public native boolean booleanValue(String key);
    public native long jsonValue(String key);

    public JSONObject jsonObjectValue(String key){
        JSONObject jsonObject = new JSONObject(jsonValue(key));
        jsonObject.setObjectPtr(jClassName(JSONObject.class), "objectPtr", jLong);
        return jsonObject;
    }

    /**
     * jni层深拷贝objectPtr指向的对象
     * @param objectPtr
     * @return
     */
    public static native long deepCopy(long objectPtr);
    static {
        long so = NativeLoad.loadSo("libMeCloud.so");

        registJNIMethod(so, "com/rex/mecloud/MeObject", "create", "(Ljava/lang/String;)J");
        registJNIMethod(so, "com/rex/mecloud/MeObject", "destroy", "()V");
        registJNIMethod(so, "com/rex/mecloud/MeObject", "save", "(Lcom/rex/mecloud/MeCallback;)V");

        registJNIMethod(so, "com/rex/mecloud/MeObject", "putString", "(Ljava/lang/String;Ljava/lang/String;)V");
        registJNIMethod(so, jClassName(MeObject.class), "putDouble", getMethodSigned(jString,jDouble,jVoid));
        registJNIMethod(so, jClassName(MeObject.class), "putInt", getMethodSigned(jString,jInt,jVoid));
        registJNIMethod(so, jClassName(MeObject.class), "putLong", getMethodSigned(jString,jLong,jVoid));
        registJNIMethod(so, jClassName(MeObject.class), "putFloat", getMethodSigned(jString,jFloat,jVoid));
        registJNIMethod(so, jClassName(MeObject.class), "putBoolean", getMethodSigned(jString,jBoolen,jVoid));
//        NativeLoad.registJNIMethod(so, jClassName(MeObject.class), "putObject", getMethodSigned(jString,jDouble,jVoid));

        registJNIMethod(so, "com/rex/mecloud/MeObject", "stringValue", "(Ljava/lang/String;)Ljava/lang/String;");
        registJNIMethod(so, jClassName(MeObject.class), "doubleValue", getMethodSigned(jString,jDouble));
        registJNIMethod(so, jClassName(MeObject.class), "intValue", getMethodSigned(jString,jInt));
        registJNIMethod(so, jClassName(MeObject.class), "longValue", getMethodSigned(jString,jLong));
        registJNIMethod(so, jClassName(MeObject.class), "floatValue", getMethodSigned(jString,jFloat));
        registJNIMethod(so, jClassName(MeObject.class), "booleanValue", getMethodSigned(jString,jBoolen));
        registJNIMethod(so, jClassName(MeObject.class), "jsonValue", getMethodSigned(jString,jLong));
    }

    @Override
    public int describeContents() {
        return 0;
    }

    @Override
    public void writeToParcel(Parcel parcel, int i) {
        parcel.writeLong(objectPtr);
        parcel.writeString(className);
    }

    public static final Creator<MeObject> CREATOR = new Creator<MeObject>() {
        @Override
        public MeObject createFromParcel(Parcel in) {
            return new MeObject(in);
        }

        @Override
        public MeObject[] newArray(int size) {
            return new MeObject[size];
        }
    };
}
