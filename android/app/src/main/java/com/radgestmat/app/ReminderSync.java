package com.radgestmat.app;

import android.content.*;
import android.webkit.CookieManager;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public final class ReminderSync {
    public static final String BASE = "https://radgestmat.onrender.com";
    private final Context context;
    private final SharedPreferences credentials;
    public ReminderSync(Context c) {
        context = c.getApplicationContext();
        credentials = context.getSharedPreferences("device", Context.MODE_PRIVATE);
    }
    // All methods are called on a background thread; serialize enrollment and sync.
    public static synchronized void run(Context c) throws Exception {
        new ReminderSync(c).sync();
    }
    public static synchronized boolean ensureEnrolled(Context c) throws Exception {
        ReminderSync client = new ReminderSync(c);
        if (client.credentials.contains("token")) return true;
        JSONObject session = client.request("device/session/", "GET", "", "");
        // Older servers do not advertise safe enrollment: do not replace an unknown device.
        if (!session.has("device_registered")) throw new IOException("Server upgrade required");
        if (session.getBoolean("device_registered")) return false;
        try {
            client.register(session, false);
            return true;
        } catch (DeviceConflict e) { return false; }
    }
    private static class DeviceConflict extends IOException {}
    public static synchronized void enroll(Context c) throws Exception {
        ReminderSync client = new ReminderSync(c);
        JSONObject session = client.request("device/session/", "GET", "", "");
        client.register(session, true);
    }
    private void register(JSONObject session, boolean replace) throws Exception {
        JSONObject response = request("device/register/" + (replace ? "" : "?replace=0"), "POST", session.getString("csrf"), "");
        String token = response.getString("device_token");
        long user = response.getLong("user_id");
        new ReminderEngine(context).clear();
        credentials.edit().putString("token", token).putLong("user", user).commit();
        sync();
    }
    public static synchronized void clear(Context c) {
        new ReminderSync(c).credentials.edit().clear().commit();
        new ReminderEngine(c).clear();
    }
    private void sync() throws Exception {
        if (!credentials.contains("token")) return;
        JSONObject snapshot = request("personal/", "GET", "", credentials.getString("token", ""));
        if (snapshot.getLong("user_id") != credentials.getLong("user", -1)) {
            clear(context); return;
        }
        new ReminderEngine(context).replaceSnapshot(snapshot.getJSONArray("reminders"));
    }
    private JSONObject request(String path, String method, String csrf, String token) throws Exception {
        String url = BASE + "/api/reminders/" + path;
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        try {
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(20000);
            connection.setReadTimeout(20000);
            connection.setRequestMethod(method);
            connection.setRequestProperty("Accept", "application/json");
            String cookies = CookieManager.getInstance().getCookie(url);
            if (cookies != null) connection.setRequestProperty("Cookie", cookies);
            if (!token.isEmpty()) connection.setRequestProperty("X-Reminder-Device", token);
            if ("POST".equals(method)) {
                connection.setRequestProperty("X-CSRFToken", csrf);
                connection.setRequestProperty("Origin", BASE);
                connection.setRequestProperty("Referer", BASE + "/");
                connection.setDoOutput(true);
                connection.setFixedLengthStreamingMode(0);
                connection.getOutputStream().close();
            }
            int status = connection.getResponseCode();
            if (status == 409) throw new DeviceConflict();
            if (status == 401 || status == 403) {
                if ("GET".equals(method)) clear(context);
                throw new IOException("Authentication or device authorization required");
            }
            if (status != 200) throw new IOException("HTTP " + status);
            try (InputStream input = connection.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096]; int count;
                while ((count = input.read(buffer)) != -1) {
                    if (out.size() + count > 8 * 1024 * 1024) throw new IOException("Snapshot too large");
                    out.write(buffer, 0, count);
                }
                return new JSONObject(new String(out.toByteArray(), StandardCharsets.UTF_8));
            }
        } finally { connection.disconnect(); }
    }
}
