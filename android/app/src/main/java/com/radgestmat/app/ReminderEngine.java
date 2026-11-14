package com.radgestmat.app;

import android.app.*;
import android.content.*;
import android.net.Uri;
import org.json.*;

public final class ReminderEngine {
    static final long INTERVAL = 15 * 60 * 1000L;
    private final Context context;
    private final SharedPreferences store;
    private final AlarmManager alarms;

    public ReminderEngine(Context context) {
        this.context = context.getApplicationContext();
        store = this.context.getSharedPreferences("reminders", Context.MODE_PRIVATE);
        alarms = this.context.getSystemService(AlarmManager.class);
    }

    private PendingIntent intent(String id) {
        Intent i = new Intent(context, ReminderReceiver.class);
        i.setData(Uri.parse("radgestmat://reminder/" + Uri.encode(id)));
        return PendingIntent.getBroadcast(context, 0, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    JSONObject get(String id) {
        try { return new JSONObject(store.getString(id, "")); }
        catch (JSONException e) { return null; }
    }

    public void replaceSnapshot(JSONArray items) throws JSONException {
        // Validate the complete response before changing local state.
        JSONObject next = new JSONObject();
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.getJSONObject(i);
            String id = String.valueOf(item.getLong("id"));
            java.time.OffsetDateTime.parse(item.getString("deadline"));
            item.getString("asset_id");
            next.put(id, item);
        }
        for (String id : store.getAll().keySet()) {
            if (!next.has(id)) cancel(id);
        }
        java.util.Iterator<String> keys = next.keys();
        while (keys.hasNext()) {
            String id = keys.next();
            JSONObject item = next.getJSONObject(id);
            JSONObject previous = get(id);
            if (previous != null && previous.optString("deadline").equals(item.getString("deadline"))) continue;
            cancel(id);
            store.edit().putString(id, item.toString()).commit();
            schedule(id, Math.max(System.currentTimeMillis(), deadline(item)));
        }
    }

    static long deadline(JSONObject item) {
        return java.time.OffsetDateTime.parse(item.optString("deadline")).toInstant().toEpochMilli();
    }

    void schedule(String id, long when) {
        if (android.os.Build.VERSION.SDK_INT < 31 || alarms.canScheduleExactAlarms()) {
            try { alarms.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when, intent(id)); return; }
            catch (SecurityException ignored) {}
        }
        alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when, intent(id));
    }

    void cancel(String id) {
        store.edit().remove(id).commit();
        alarms.cancel(intent(id));
        context.getSystemService(NotificationManager.class).cancel(id, 1);
    }

    public void clear() {
        for (String id : store.getAll().keySet()) cancel(id);
    }

    public void restore() {
        for (String id : store.getAll().keySet()) {
            JSONObject item = get(id);
            if (item != null) schedule(id, Math.max(System.currentTimeMillis(), deadline(item)));
        }
    }
}
