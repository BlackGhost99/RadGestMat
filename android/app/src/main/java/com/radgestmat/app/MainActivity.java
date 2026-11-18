package com.radgestmat.app;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.webkit.*;
import android.view.WindowInsets;
import android.widget.*;

public class MainActivity extends Activity {
    private WebView web;
    private AppUpdater updater;
    private boolean enrollmentRunning;
    private boolean enrollmentConflictShown;
    private boolean loggedInPage;
    private boolean notificationAllowed() {
        return Build.VERSION.SDK_INT < 33 ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }
    private void ensureReminders() {
        if (!loggedInPage || !notificationAllowed() || enrollmentRunning) return;
        enrollmentRunning = true;
        new Thread(() -> {
            try {
                boolean active = ReminderSync.ensureEnrolled(this);
                runOnUiThread(() -> {
                    enrollmentRunning = false;
                    if (active && loggedInPage && !isFinishing()) requestExactAlarmOnce();
                    if (!active && !enrollmentConflictShown && loggedInPage && !isFinishing()) {
                        enrollmentConflictShown = true;
                        new AlertDialog.Builder(this)
                            .setMessage("Un autre téléphone reçoit déjà vos rappels. Les transférer vers celui-ci ?")
                            .setNegativeButton("Non", null)
                            .setPositiveButton("Transférer", (d,w) -> enroll()).show();
                    }
                });
            } catch (Exception e) {
                runOnUiThread(() -> enrollmentRunning = false);
            }
        }).start();
    }
    private boolean trusted(Uri uri) {
        return "https".equals(uri.getScheme()) && "radgestmat.onrender.com".equals(uri.getHost())
            && (uri.getPort() == -1 || uri.getPort() == 443);
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        updater = new AppUpdater(this);
        FrameLayout layout = new FrameLayout(this);
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            layout.setOnApplyWindowInsetsListener((view, insets) -> {
                android.graphics.Insets bars = insets.getInsets(
                    WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                return insets;
            });
        }
        web = new WebView(this);
        layout.addView(web, new FrameLayout.LayoutParams(-1, -1));
        setContentView(layout);
        layout.requestApplyInsets();
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,false);
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (request.isForMainFrame() && "GET".equals(request.getMethod()) && trusted(request.getUrl())) {
                    WebResourceResponse local = OfflinePages.serve(MainActivity.this, request.getUrl());
                    if (local != null) return local;
                }
                return super.shouldInterceptRequest(view, request);
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!trusted(uri)) return true;
                if ("/logout/".equals(uri.getPath()) || "/login/".equals(uri.getPath())) {
                    new Thread(() -> { ReminderSync.clear(MainActivity.this); OfflineSyncWorker.clear(MainActivity.this); }).start();
                }
                return false;
            }
            @Override public void onPageFinished(WebView view, String url) {
                CookieManager.getInstance().flush();
                Uri uri = Uri.parse(url);
                if (trusted(uri) && ("/logout/".equals(uri.getPath()) || "/login/".equals(uri.getPath()))) {
                    loggedInPage = false;
                    enrollmentConflictShown = false;
                    new Thread(() -> { ReminderSync.clear(MainActivity.this); OfflineSyncWorker.clear(MainActivity.this); }).start();
                } else if (trusted(uri)) {
                    loggedInPage = true;
                    ensureReminders();
                    ReminderSyncWorker.refresh(MainActivity.this);
                    OfflineSyncWorker.refresh(MainActivity.this);
                }
            }
        });
        openIntent(getIntent());
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED && !getPreferences(MODE_PRIVATE).getBoolean("notification_permission_requested", false)) {
            getPreferences(MODE_PRIVATE).edit().putBoolean("notification_permission_requested", true).apply();
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
        }
        ReminderSyncWorker.schedule(this);
        OfflineSyncWorker.schedule(this);
        OfflineSyncWorker.refresh(this);
    }
    private void openIntent(Intent intent) {
        Uri uri = intent == null ? null : intent.getData();
        String path = uri == null ? null : uri.getPath();
        if (uri != null && trusted(uri) && path != null &&
                (path.startsWith("/scan/") || path.startsWith("/materiel/"))) {
            web.loadUrl(uri.toString());
        } else {
            web.loadUrl(ReminderSync.BASE + "/");
        }
    }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        openIntent(intent);
    }
    private void enroll() {
        new Thread(() -> {
            try {
                ReminderSync.enroll(this);
                runOnUiThread(() -> { Toast.makeText(this,"Téléphone activé",Toast.LENGTH_LONG).show(); requestExactAlarmOnce(); });
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(this,"Activation impossible. Vérifiez votre connexion et votre compte.",Toast.LENGTH_LONG).show());
            }
        }).start();
    }
    private void requestExactAlarmOnce() {
        if (Build.VERSION.SDK_INT >= 31 && !getSystemService(AlarmManager.class).canScheduleExactAlarms()
                && !getPreferences(MODE_PRIVATE).getBoolean("exact_alarm_requested", false)) {
            getPreferences(MODE_PRIVATE).edit().putBoolean("exact_alarm_requested", true).apply();
            try { startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:"+getPackageName()))); }
            catch (ActivityNotFoundException ignored) {}
        }
    }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode,permissions,results);
        if (requestCode == 1 && results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) { ensureReminders(); ReminderSyncWorker.refresh(this); }
    }
    @Override protected void onResume() {
        super.onResume();
        if (updater != null) updater.resume();
        OfflineSyncWorker.refresh(this);
        ensureReminders();
        ReminderSyncWorker.refresh(this);
    }
    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
