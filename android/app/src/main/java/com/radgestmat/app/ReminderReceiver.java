package com.radgestmat.app;

import android.app.*;
import android.content.*;
import android.media.*;
import org.json.JSONObject;

public class ReminderReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (intent.getData() == null) return;
        String id = intent.getData().getLastPathSegment();
        ReminderEngine engine = new ReminderEngine(context);
        JSONObject item = engine.get(id);
        if (item == null) return;
        long now = System.currentTimeMillis();
        if (now < ReminderEngine.deadline(item)) {
            engine.schedule(id, ReminderEngine.deadline(item)); return;
        }
        // Dismissing the notification never cancels the outstanding loan.
        engine.schedule(id, now + ReminderEngine.INTERVAL);
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        NotificationChannel channel = new NotificationChannel("loan_due", "Retours de matériel", NotificationManager.IMPORTANCE_HIGH);
        channel.enableVibration(true);
        channel.setVibrationPattern(new long[]{0, 500, 250, 500});
        channel.setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION),
            new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION).build());
        manager.createNotificationChannel(channel);
        Notification notification = new Notification.Builder(context, "loan_due")
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("Retour de matériel attendu")
            .setContentText(item.optString("asset_id"))
            .setOnlyAlertOnce(false).setAutoCancel(true).build();
        try { manager.notify(id, 1, notification); } catch (SecurityException ignored) {}
    }
}
