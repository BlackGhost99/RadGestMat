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
    public static synchronized void enroll(Context c) throws Exception {
        ReminderSync client = new ReminderSync(c);
        JSONObject session = client.request("device/session/", "GET", "", "");
        JSONObject response = client.request("device/register/", "POST", session.getString("csrf"), "");
        String token = response.getString("device_token");
        long user = response.getLong("user_id");
        new ReminderEngine(c).clear();
        client.credentials.edit().putString("token", token).putLong("user", user).commit();
        client.sync();
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
