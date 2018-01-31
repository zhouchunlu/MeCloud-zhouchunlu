package com.rex.mecloud;

/**
 * Created by Rex on 17/7/20.
 */

public class MeQuery {
    public long             objectPtr   =0;
    protected String        className   = null;

    public MeQuery(String className){
        this.className = className;
        objectPtr = createQuery(className);
    }

    @Override
    protected void finalize() throws Throwable {
        super.finalize();
        // 销毁jni层动态创建的MeQuery
        destroyQuery();
    }

    /**
     * 异步get回调接口， jni中调用
     * @param callback
     */
    public void getCallback(final long jniObject, final MeCallback callback, final MeException err){
        final MeObject obj = new MeObject(className);
        obj.objectPtr = MeObject.deepCopy(jniObject);
        MeCloud.shareInstance().post(new Runnable() {
            @Override
            public void run() {
                callback.done(obj, err);
            }
        });
    }
    public void findCallback(final long[] jniObjects, final MeListCallback callback, final MeException err){
        final MeObject[] objs = new MeObject[jniObjects.length];
        if (err==null) {
            for (int i = 0; i < objs.length; i++) {
                objs[i].className = className;
                objs[i].objectPtr = MeObject.deepCopy(jniObjects[i]);
            }
        }

        MeCloud.shareInstance().post(new Runnable() {
            @Override
            public void run() {
                callback.done(objs, err);
            }
        });
    }

    public native long createQuery(String className);
    protected native void destroyQuery();

    public native void whereEqualTo(String key, String val);
    public native void whereNotEqualTo(String key, String val);
    public native void whereEqualTo(String key, int value);
    public native void whereNotEqualTo(String key, int value);
    public native void selectKeys(String keys[], int num);
    public native void addSelectKey(String key);

    public native void get(String objectId, MeCallback callback);
    public native void find(MeListCallback callback);
}
