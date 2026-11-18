package com.radgestmat.app;
import android.content.Context;
import android.webkit.CookieManager;
import androidx.work.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

public class OfflineSyncWorker extends Worker {
    private static final Object LOCK=new Object();
    public OfflineSyncWorker(Context c,WorkerParameters p){super(c,p);}
    public static void clear(Context c){
        synchronized(LOCK){try(OfflineStore store=new OfflineStore(c)){store.clear();}}
    }
    @Override public Result doWork(){
        synchronized(LOCK){
            String session=OfflineStore.session();
            try(OfflineStore store=new OfflineStore(getApplicationContext())){
                if(session.isEmpty()){store.clear();return Result.success();}
                if(!store.usable(session))store.clear();
                if(store.usable(session)&&System.currentTimeMillis()-store.updated()<15000)return Result.success();
                String url=ReminderSync.BASE+"/api/offline/v1/snapshot/";
                HttpURLConnection conn=(HttpURLConnection)new URL(url).openConnection();
                try{
                    conn.setConnectTimeout(20000);conn.setReadTimeout(25000);conn.setInstanceFollowRedirects(false);
                    String cookie=CookieManager.getInstance().getCookie(url);
                    if(cookie==null)return Result.success();
                    conn.setRequestProperty("Cookie",cookie);conn.setRequestProperty("Accept","application/json");
                    String etag=store.etag(session);if(!etag.isEmpty())conn.setRequestProperty("If-None-Match",etag);
                    int status=conn.getResponseCode();
                    if(!session.equals(OfflineStore.session()))return Result.success();
                    if(status==401||status==403||status==302){store.clear();return Result.success();}
                    if(status==304){store.touch(session);return Result.success();}
                    if(status!=200)return Result.retry();
                    try(InputStream in=conn.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
                        byte[] b=new byte[8192];int n;
                        while((n=in.read(b))!=-1){if(out.size()+n>8*1024*1024)return Result.failure();out.write(b,0,n);}
                        JSONObject payload=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));
                        if(session.equals(OfflineStore.session()))store.replace(payload,session,conn.getHeaderField("ETag")==null?"":conn.getHeaderField("ETag"));
                    }
                    return Result.success();
                }finally{conn.disconnect();}
            }catch(Exception e){return Result.retry();}
        }
    }
    private static Constraints network(){return new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();}
    static void refresh(Context c){WorkManager.getInstance(c).enqueueUniqueWork("offline-refresh",ExistingWorkPolicy.KEEP,new OneTimeWorkRequest.Builder(OfflineSyncWorker.class).setConstraints(network()).build());}
    static void schedule(Context c){WorkManager.getInstance(c).enqueueUniquePeriodicWork("offline-periodic",ExistingPeriodicWorkPolicy.KEEP,new PeriodicWorkRequest.Builder(OfflineSyncWorker.class,15,TimeUnit.MINUTES).setConstraints(network()).build());}
}
