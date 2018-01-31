package com.rex.mecloud;

import android.os.Parcel;
import android.os.Parcelable;
import android.util.Log;

import com.rex.load.NativeLoad;

import static com.rex.load.NativeLoad.registJNIMethod;
import static com.rex.utils.SignedUtil.getMethodSigned;
import static com.rex.utils.SignedUtil.jBoolen;
import static com.rex.utils.SignedUtil.jClassName;
import static com.rex.utils.SignedUtil.jDouble;
import static com.rex.utils.SignedUtil.jFloat;
import static com.rex.utils.SignedUtil.jInt;
import static com.rex.utils.SignedUtil.jLong;
import static com.rex.utils.SignedUtil.jString;

/**
 * Project Name:android
 * Author:CoorChice
 * Date:2017/7/21
 * Notes:
 */

public class JSONObject implements Parcelable {
  public long             objectPtr   =0;

  public native void setObjectPtr(String jclassname, String jfieldname, String jsign);
  protected native void destroy();

  public native String stringValue(String key);
  public native double doubleValue(String key);
  public native int intValue(String key);
  public native long longValue(String key);
  public native float floatValue(String key);
  public native boolean booleanValue(String key);
  public native long jsonValue(String key);

  static {
    long so = NativeLoad.loadSo("libMeCloud.so");

    registJNIMethod(so, jClassName(JSONObject.class), "setObjectPtr", getMethodSigned(jString,jString,jString));
    registJNIMethod(so, jClassName(JSONObject.class), "destroy", getMethodSigned());

    registJNIMethod(so, jClassName(JSONObject.class), "stringValue", getMethodSigned(jString,jString));
    registJNIMethod(so, jClassName(JSONObject.class), "doubleValue", getMethodSigned(jString,jDouble));
    registJNIMethod(so, jClassName(JSONObject.class), "intValue", getMethodSigned(jString,jInt));
    registJNIMethod(so, jClassName(JSONObject.class), "longValue", getMethodSigned(jString,jLong));
    registJNIMethod(so, jClassName(JSONObject.class), "floatValue", getMethodSigned(jString,jFloat));
    registJNIMethod(so, jClassName(JSONObject.class), "booleanValue", getMethodSigned(jString,jBoolen));
    registJNIMethod(so, jClassName(JSONObject.class), "jsonValue", getMethodSigned(jString,jLong));

  }

  public JSONObject(long objectPtr){
    this.objectPtr = objectPtr;
    Log.e("obj", "ptr: "+objectPtr);
  }

  protected JSONObject(Parcel in) {
    objectPtr = in.readLong();
  }

  public static final Creator<JSONObject> CREATOR = new Creator<JSONObject>() {
    @Override
    public JSONObject createFromParcel(Parcel in) {
      return new JSONObject(in);
    }

    @Override
    public JSONObject[] newArray(int size) {
      return new JSONObject[size];
    }
  };

  @Override
  public int describeContents() {
    return 0;
  }

  @Override
  public void writeToParcel(Parcel dest, int flags) {
    dest.writeLong(objectPtr);
  }

  @Override
  protected void finalize() throws Throwable {
    super.finalize();
    destroy();
  }
}
