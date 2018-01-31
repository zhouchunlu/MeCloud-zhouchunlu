//package com.rex.mecloud;
//
//import static com.rex.load.NativeLoad.registJNIMethod;
//import static com.rex.utils.SignedUtil.getMethodSigned;
//import static com.rex.utils.SignedUtil.jBoolen;
//import static com.rex.utils.SignedUtil.jClassName;
//import static com.rex.utils.SignedUtil.jDouble;
//import static com.rex.utils.SignedUtil.jFloat;
//import static com.rex.utils.SignedUtil.jInt;
//import static com.rex.utils.SignedUtil.jLong;
//import static com.rex.utils.SignedUtil.jString;
//
//import com.rex.load.NativeLoad;
//
//import android.os.Parcel;
//import android.os.Parcelable;
//import android.util.Log;
//
///**
// * Project Name:android
// * Author:CoorChice
// * Date:2017/7/21
// * Notes:
// */
//
//public class JSONArray implements Parcelable {
//  public long             objectPtr   =0;
//
//  public native void setObjectPtr(String jclassname, String jfieldname, String jsign);
//  protected native void destroy();
//
//  public native String stringValue(String key);
//  public native double doubleValue(String key);
//  public native int intValue(String key);
//  public native long longValue(String key);
//  public native float floatValue(String key);
//  public native boolean booleanValue(String key);
//  public native long jsonValue(String key);
//
//  static {
//    long so = NativeLoad.loadSo("libMeCloud.so");
//
//    registJNIMethod(so, jClassName(JSONArray.class), "setObjectPtr", getMethodSigned(jString,jString,jString));
//    registJNIMethod(so, jClassName(JSONArray.class), "destroy", getMethodSigned());
//
//    registJNIMethod(so, jClassName(JSONArray.class), "stringValue", getMethodSigned(jString,jString));
//    registJNIMethod(so, jClassName(JSONArray.class), "doubleValue", getMethodSigned(jString,jDouble));
//    registJNIMethod(so, jClassName(JSONArray.class), "intValue", getMethodSigned(jString,jInt));
//    registJNIMethod(so, jClassName(JSONArray.class), "longValue", getMethodSigned(jString,jLong));
//    registJNIMethod(so, jClassName(JSONArray.class), "floatValue", getMethodSigned(jString,jFloat));
//    registJNIMethod(so, jClassName(JSONArray.class), "booleanValue", getMethodSigned(jString,jBoolen));
//    registJNIMethod(so, jClassName(JSONArray.class), "jsonValue", getMethodSigned(jString,jLong));
//
//  }
//
//  public JSONArray(long objectPtr){
//    this.objectPtr = objectPtr;
//    Log.e("obj", "ptr: "+objectPtr);
//  }
//
//  protected JSONArray(Parcel in) {
//    objectPtr = in.readLong();
//  }
//
//  public static final Creator<JSONArray> CREATOR = new Creator<JSONArray>() {
//    @Override
//    public JSONArray createFromParcel(Parcel in) {
//      return new JSONArray(in);
//    }
//
//    @Override
//    public JSONArray[] newArray(int size) {
//      return new JSONArray[size];
//    }
//  };
//
//  @Override
//  public int describeContents() {
//    return 0;
//  }
//
//  @Override
//  public void writeToParcel(Parcel dest, int flags) {
//    dest.writeLong(objectPtr);
//  }
//
//  @Override
//  protected void finalize() throws Throwable {
//    super.finalize();
//    destroy();
//  }
//}
