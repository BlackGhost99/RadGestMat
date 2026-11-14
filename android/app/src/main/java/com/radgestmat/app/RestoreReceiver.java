package com.radgestmat.app;
import android.content.*;
public class RestoreReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        new ReminderEngine(context).restore();
    }
}
