package com.rex.medemo;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import com.rex.mecloud.MeCallback;
import com.rex.mecloud.MeException;
import com.rex.mecloud.MeObject;

public class MainActivity extends AppCompatActivity{

    private TextView tv;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        tv = (TextView) findViewById(R.id.tv);
        MeObject obj = new MeObject("Test");
        obj.put("key_string", "testtest");
        obj.put("key_double", 0.9999d);
        obj.put("key_int", 100);
        obj.put("key_long", 10000l);
        obj.put("key_float", 0.99);
        obj.put("key_boolean", true);

        obj.save(new MeCallback() {
            @Override
            public void done(MeObject obj, MeException err) {
                if (err==null){
                    StringBuffer sb = new StringBuffer();
                    sb.append("done: " + obj.stringValue("_id") + "\n");
                    sb.append("doneString: " + obj.stringValue("key_string") + "\n");
                    sb.append("doneDouble: " + String.valueOf(obj.doubleValue("key_double")) + "\n");
                    sb.append("doneInt: " + String.valueOf(obj.intValue("key_int")) + "\n");
                    sb.append("doneLong: " + String.valueOf(obj.longValue("key_long")) + "\n");
                    sb.append("doneFloat: " + String.valueOf(obj.floatValue("key_float")) + "\n");
                    sb.append("doneBoolean: " + String.valueOf( obj.booleanValue("key_boolean")) + "\n");
                    tv.setText(sb.toString());

                    Log.e("done", obj.stringValue("_id"));
                    Log.e("doneString", obj.stringValue("key_string"));
                    Log.e("doneDouble", String.valueOf(obj.doubleValue("key_double")));
                    Log.e("doneInt", String.valueOf(obj.intValue("key_int")));
                    Log.e("doneLong", String.valueOf(obj.longValue("key_long")));
                    Log.e("doneFloat", String.valueOf(obj.floatValue("key_float")));
                    Log.e("doneBoolean",String.valueOf( obj.booleanValue("key_boolean")));

                }
            }
        });
    }
}
