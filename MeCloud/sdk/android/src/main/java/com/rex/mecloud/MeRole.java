package com.rex.mecloud;

/**
 * Created by Visionin on 17/7/18.
 */

public class MeRole extends MeObject{
    public MeRole(){
        super("Role");
    }

    public void setUser(MeUser user){
        setUser(user.objectId());
    }

    public native void setUser(String userId);
}
