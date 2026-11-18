package com.radgestmat.app;

import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.widget.Toast;
import androidx.core.content.FileProvider;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import org.json.JSONObject;

final class AppUpdater {
    private static final String BASE="https://github.com/BlackGhost99/RadGestMat/releases/";
    private final Activity activity;
    private boolean busy, prompted;
    private File pending;
    AppUpdater(Activity activity){this.activity=activity;}
    void check(){
        if(busy||prompted||activity.isFinishing())return;
        busy=true;
        new Thread(()->{
            JSONObject info=null;
            try{
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                fetch(BASE+"latest/download/update.json",out,16384);
                JSONObject value=new JSONObject(out.toString("UTF-8"));
                int code=value.getInt("version_code");
                if(code>installedCode()&&value.getString("sha256").matches("[a-fA-F0-9]{64}")&&value.getLong("size")>0&&value.getLong("size")<=100L*1024*1024)info=value;
            }catch(Exception ignored){}
            final JSONObject update=info;
            activity.runOnUiThread(()->{
                busy=false;
                if(update==null||activity.isFinishing()||activity.isDestroyed())return;
                prompted=true;
                new AlertDialog.Builder(activity).setTitle("Nouvelle mise à jour")
                    .setMessage("RadGestMat "+update.optString("version_name")+" est disponible. Vos données seront conservées.")
                    .setNegativeButton("Plus tard",null)
                    .setPositiveButton("Installer",(d,w)->download(update)).show();
            });
        }).start();
    }
    private long installedCode()throws Exception{
        PackageInfo p=activity.getPackageManager().getPackageInfo(activity.getPackageName(),0);
        return Build.VERSION.SDK_INT>=28?p.getLongVersionCode():p.versionCode;
    }
    private void download(JSONObject info){
        if(busy)return;
        busy=true;
        Toast.makeText(activity,"Téléchargement de la mise à jour…",Toast.LENGTH_LONG).show();
        new Thread(()->{
            File apk=null;
            try{
                File dir=new File(activity.getCacheDir(),"updates");if(!dir.exists()&&!dir.mkdirs())throw new IOException("Storage");
                apk=new File(dir,"RadGestMat.apk");
                try(FileOutputStream out=new FileOutputStream(apk)){
                    fetch(BASE+"download/android-v"+info.getInt("version_code")+"/RadGestMat.apk",out,info.getLong("size"));
                }
                if(apk.length()!=info.getLong("size")||!digest(apk).equalsIgnoreCase(info.getString("sha256")))throw new IOException("Invalid digest");
                verify(apk,info.getInt("version_code"));
                final File ready=apk;
                activity.runOnUiThread(()->{busy=false;pending=ready;installPending();});
            }catch(Exception e){
                if(apk!=null)apk.delete();
                activity.runOnUiThread(()->{busy=false;prompted=false;Toast.makeText(activity,"Mise à jour indisponible ou signature incompatible.",Toast.LENGTH_LONG).show();});
            }
        }).start();
    }
    private void verify(File apk,int version)throws Exception{
        PackageManager pm=activity.getPackageManager();
        int flags=Build.VERSION.SDK_INT>=28?PackageManager.GET_SIGNING_CERTIFICATES:PackageManager.GET_SIGNATURES;
        PackageInfo old=pm.getPackageInfo(activity.getPackageName(),flags),next=pm.getPackageArchiveInfo(apk.getAbsolutePath(),flags);
        if(next==null||!activity.getPackageName().equals(next.packageName))throw new IOException("Wrong package");
        long code=Build.VERSION.SDK_INT>=28?next.getLongVersionCode():next.versionCode;
        if(code!=version||code<=installedCode())throw new IOException("Wrong version");
        Signature[] before=Build.VERSION.SDK_INT>=28?old.signingInfo.getApkContentsSigners():old.signatures;
        Signature[] after=Build.VERSION.SDK_INT>=28?next.signingInfo.getApkContentsSigners():next.signatures;
        if(before==null||after==null||before.length!=1||after.length!=1||!before[0].equals(after[0]))throw new IOException("Wrong signature");
    }
    void resume(){if(pending!=null&&activity.getPackageManager().canRequestPackageInstalls())installPending();else check();}
    private void installPending(){
        if(pending==null||activity.isFinishing()||activity.isDestroyed())return;
        if(!activity.getPackageManager().canRequestPackageInstalls()){
            new AlertDialog.Builder(activity).setTitle("Autorisation Android")
                .setMessage("Autorisez RadGestMat à installer ses mises à jour. Android demandera ensuite votre confirmation.")
                .setNegativeButton("Plus tard",(d,w)->{pending=null;prompted=false;})
                .setPositiveButton("Autoriser",(d,w)->{
                    try{activity.startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+activity.getPackageName())));}
                    catch(Exception e){pending=null;prompted=false;}
                }).show();return;
        }
        File ready=pending;pending=null;
        try{
            Uri uri=FileProvider.getUriForFile(activity,activity.getPackageName()+".updates",ready);
            activity.startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(uri,"application/vnd.android.package-archive").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));
        }catch(Exception e){prompted=false;Toast.makeText(activity,"Installation impossible.",Toast.LENGTH_LONG).show();}
    }
    private static String digest(File file)throws Exception{
        MessageDigest d=MessageDigest.getInstance("SHA-256");byte[] b=new byte[8192];
        try(InputStream in=new FileInputStream(file)){int n;while((n=in.read(b))!=-1)d.update(b,0,n);}
        StringBuilder s=new StringBuilder();for(byte x:d.digest())s.append(String.format(java.util.Locale.ROOT,"%02x",x&255));return s.toString();
    }
    private static void fetch(String address,OutputStream out,long max)throws Exception{
        URL url=new URL(address);
        for(int i=0;i<6;i++){
            String host=url.getHost();
            if(!"https".equals(url.getProtocol())||!(host.equals("github.com")||host.equals("release-assets.githubusercontent.com")||host.equals("objects.githubusercontent.com"))||url.getUserInfo()!=null||(url.getPort()!=-1&&url.getPort()!=443))throw new IOException("Untrusted host");
            HttpURLConnection conn=(HttpURLConnection)url.openConnection();
            try{
                conn.setInstanceFollowRedirects(false);conn.setConnectTimeout(12000);conn.setReadTimeout(30000);
                int status=conn.getResponseCode();
                if(status>=300&&status<400){url=new URL(url,conn.getHeaderField("Location"));continue;}
                if(status!=200)throw new IOException("HTTP "+status);
                long total=0;byte[] b=new byte[8192];int n;
                try(InputStream in=conn.getInputStream()){
                    while((n=in.read(b))!=-1){total+=n;if(total>max)throw new IOException("Too large");out.write(b,0,n);}
                }return;
            }finally{conn.disconnect();}
        }throw new IOException("Too many redirects");
    }
}
