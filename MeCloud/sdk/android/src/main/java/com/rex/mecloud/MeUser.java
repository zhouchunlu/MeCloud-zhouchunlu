package com.rex.mecloud;

/**
 * Created by Visionin on 17/7/18.
 */

public class MeUser extends MeObject{
    public long     objectPtr = 0;

    public MeUser(){
        objectPtr = createUser();
        className = "User";
    }

    public static MeUser current(){
        long ptr = currentUser();
        if (ptr != 0){
            MeUser user = new MeUser();
            user.objectPtr = ptr;
            return user;
        }

        return null;
    }

    public native long createUser();
    public native void destroyUser();
    public static native long currentUser();

    public native void login(String username, String password, MeCallback callback);
    public native void signup(String username, String password, MeCallback callback);
}
