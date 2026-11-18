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
    private boolean trusted(Uri uri) {
        return "https".equals(uri.getScheme()) && "radgestmat.onrender.com".equals(uri.getHost())
            && (uri.getPort() == -1 || uri.getPort() == 443);
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(0,0,0,0);
        if (android.os.Build.VERSION.SDK_INT >= 35) {
            layout.setOnApplyWindowInsetsListener((v, insets) -> {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                v.setPadding(bars.left,bars.top,bars.right,bars.bottom);
                return insets;
            });
        }
        web = new WebView(this);
        layout.addView(web, new LinearLayout.LayoutParams(-1,0,1));
        setContentView(layout);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web,false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!trusted(uri)) return true;
                if ("/logout/".equals(uri.getPath()) || "/login/".equals(uri.getPath())) {
                    new Thread(() -> ReminderSync.clear(MainActivity.this)).start();
                }
                return false;
            }
            @Override public void onPageFinished(WebView view, String url) {
                CookieManager.getInstance().flush();
                Uri uri = Uri.parse(url);
                if (trusted(uri) && ("/logout/".equals(uri.getPath()) || "/login/".equals(uri.getPath()))) {
                    new Thread(() -> ReminderSync.clear(MainActivity.this)).start();
                } else if (trusted(uri)) ReminderSyncWorker.refresh(MainActivity.this);
            }
        });
        openIntent(getIntent());
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED && !getPreferences(MODE_PRIVATE).getBoolean("notification_permission_requested", false)) {
            getPreferences(MODE_PRIVATE).edit().putBoolean("notification_permission_requested", true).apply();
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
        }
        ReminderSyncWorker.schedule(this);
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
    @Override public boolean onCreateOptionsMenu(android.view.Menu menu) {
        menu.add("Activer les rappels sur ce téléphone");
        menu.add("Désactiver les rappels sur ce téléphone");
        return true;
    }
    @Override public boolean onOptionsItemSelected(android.view.MenuItem item) {
        if ("Activer les rappels sur ce téléphone".contentEquals(item.getTitle())) {
            new AlertDialog.Builder(this).setMessage("Activer ce téléphone remplacera votre ancien appareil principal.")
                .setNegativeButton("Annuler", null).setPositiveButton("Activer", (a,b) -> enroll()).show();
            return true;
        }
        if ("Désactiver les rappels sur ce téléphone".contentEquals(item.getTitle())) {
            new Thread(() -> ReminderSync.clear(this)).start();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
    private void enroll() {
        new Thread(() -> {
            try {
                ReminderSync.enroll(this);
                runOnUiThread(() -> { Toast.makeText(this,"Téléphone activé",Toast.LENGTH_LONG).show(); permissions(); });
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(this,"Activation impossible. Vérifiez votre connexion et votre compte.",Toast.LENGTH_LONG).show());
            }
        }).start();
    }
    private void permissions() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
            return;
        }
        if (Build.VERSION.SDK_INT >= 31 && !getSystemService(AlarmManager.class).canScheduleExactAlarms()) {
            try { startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,Uri.parse("package:"+getPackageName()))); }
            catch (ActivityNotFoundException ignored) {}
        } else {
            startActivity(new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE,getPackageName()));
        }
    }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode,permissions,results);
        if (requestCode == 1 && results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) ReminderSyncWorker.refresh(this);
    }
    @Override protected void onResume() {
        super.onResume();
        ReminderSyncWorker.refresh(this);
    }
    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
