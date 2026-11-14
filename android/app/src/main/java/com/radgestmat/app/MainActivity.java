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
        Button settings = new Button(this);
        settings.setText("Gestion des rappels");
        layout.addView(settings);
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
        settings.setOnClickListener(v -> new AlertDialog.Builder(this)
            .setTitle("Rappels personnels")
            .setItems(new String[]{"Activer ce téléphone principal","Synchroniser","Autorisations Android","Désactiver les rappels locaux"},(d,i) -> {
                if (i == 0) new AlertDialog.Builder(this).setMessage("Activer ce téléphone remplacera votre ancien appareil principal.")
                    .setNegativeButton("Annuler",null).setPositiveButton("Activer",(a,b)->enroll()).show();
                if (i == 1) ReminderSyncWorker.refresh(this);
                if (i == 2) permissions();
                if (i == 3) new Thread(()->ReminderSync.clear(this)).start();
            }).show());
        web.loadUrl(ReminderSync.BASE + "/");
        ReminderSyncWorker.schedule(this);
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
        if (requestCode == 1 && results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) permissions();
    }
    @Override protected void onResume() {
        super.onResume();
        ReminderSyncWorker.refresh(this);
    }
    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed();
    }
}
