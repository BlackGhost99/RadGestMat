package com.radgestmat.mobile;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.graphics.Color;

public class MainActivity extends Activity {
    private static final int CAMERA_PERMISSION = 71;
    private WebView webView;
    private EditText urlInput;
    private ValueCallback<Uri[]> fileCallback;
    private static final int FILE_PICKER = 72;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showSetup();
    }

    private void showSetup() {
        SharedPreferences prefs = getSharedPreferences("radgestmat", MODE_PRIVATE);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(28, 60, 28, 28);
        layout.setBackgroundColor(Color.WHITE);

        TextView title = new TextView(this);
        title.setText("RadGestMat Mobile");
        title.setTextSize(26);
        title.setTextColor(Color.rgb(20, 45, 80));
        layout.addView(title);

        TextView help = new TextView(this);
        help.setText("Saisissez l'adresse HTTPS de votre instance RadGestMat pour vous connecter.");
        help.setTextSize(16);
        help.setPadding(0, 20, 0, 20);
        layout.addView(help);

        urlInput = new EditText(this);
        urlInput.setSingleLine(true);
        urlInput.setHint("https://votre-instance.onrender.com");
        urlInput.setInputType( android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        urlInput.setText(prefs.getString("base_url", ""));
        layout.addView(urlInput);

        Button open = new Button(this);
        open.setText("Connecter RadGestMat");
        layout.addView(open);
        TextView note = new TextView(this);
        note.setText("Cette version de test ouvre l'interface web existante. Une connexion Internet est nécessaire ; le mode hors ligne complet n'est pas encore inclus.");
        note.setTextSize(13);
        note.setPadding(0, 24, 0, 0);
        layout.addView(note);

        open.setOnClickListener(v -> {
            String url = urlInput.getText().toString().trim();
            if (!url.startsWith("https://")) {
                urlInput.setError("Utilisez une adresse HTTPS complète.");
                return;
            }
            prefs.edit().putString("base_url", url.replaceAll("/+$", "")).apply();
            ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE))
                .hideSoftInputFromWindow(urlInput.getWindowToken(), 0);
            showWeb(url.replaceAll("/+$", "") + "/");
        });
        setContentView(layout);
    }

    private void showWeb(String url) {
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("https".equalsIgnoreCase(uri.getScheme())) return false;
                return true;
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onPermissionRequest(PermissionRequest request) {
                boolean asksCamera = false;
                for (String resource : request.getResources()) {
                    if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) asksCamera = true;
                }
                if (asksCamera && checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                    request.grant(request.getResources());
                } else if (asksCamera) {
                    requestPermission(request);
                } else {
                    request.deny();
                }
            }
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent intent = params.createIntent();
                try { startActivityForResult(intent, FILE_PICKER); }
                catch (Exception e) { fileCallback = null; return false; }
                return true;
            }
        });
        setContentView(webView);
        webView.loadUrl(url);
    }

    private PermissionRequest pendingCameraRequest;
    private void requestPermission(PermissionRequest request) {
        pendingCameraRequest = request;
        requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == CAMERA_PERMISSION && pendingCameraRequest != null) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED)
                pendingCameraRequest.grant(pendingCameraRequest.getResources());
            else pendingCameraRequest.deny();
            pendingCameraRequest = null;
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_PICKER && fileCallback != null) {
            Uri[] result = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
            fileCallback.onReceiveValue(result);
            fileCallback = null;
        }
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else if (webView != null) showSetup();
        else super.onBackPressed();
    }
}
