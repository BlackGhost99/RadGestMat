package com.radgestmat.app;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.*;
import android.webkit.CookieManager;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

final class OfflineStore extends SQLiteOpenHelper {
    static final String[] SECTIONS = {"materials","clients","categories","alerts","loans"};
    static final long TTL = 24L*60*60*1000;
    OfflineStore(Context c) { super(c.getApplicationContext(),"radgestmat_offline.db",null,1); }
    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE snapshot(section TEXT NOT NULL,id INTEGER NOT NULL,data TEXT NOT NULL,PRIMARY KEY(section,id))");
        db.execSQL("CREATE TABLE metadata(k TEXT PRIMARY KEY,v TEXT NOT NULL)");
    }
    @Override public void onUpgrade(SQLiteDatabase db,int a,int b) {
        db.execSQL("DROP TABLE snapshot");db.execSQL("DROP TABLE metadata");onCreate(db);
    }
    static String session() {
        try {
            String cookies=CookieManager.getInstance().getCookie(ReminderSync.BASE+"/");
            if(cookies==null)return "";
            for(String cookie:cookies.split(";")){
                String value=cookie.trim();
                if(value.startsWith("sessionid=")&&value.length()>10){
                    byte[] digest=MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
                    StringBuilder hex=new StringBuilder();
                    for(byte b:digest)hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
                    return hex.toString();
                }
            }
        }catch(Exception ignored){}
        return "";
    }
    private String meta(SQLiteDatabase db,String key){
        try(Cursor c=db.rawQuery("SELECT v FROM metadata WHERE k=?",new String[]{key})){return c.moveToFirst()?c.getString(0):"";}
    }
    private void put(SQLiteDatabase db,String key,String value){
        ContentValues cv=new ContentValues();cv.put("k",key);cv.put("v",value);db.insertWithOnConflict("metadata",null,cv,SQLiteDatabase.CONFLICT_REPLACE);
    }
    long updated(){try{return Long.parseLong(meta(getReadableDatabase(),"updated"));}catch(Exception e){return 0;}}
    boolean usable(String session){
        long age=System.currentTimeMillis()-updated();
        return !session.isEmpty()&&session.equals(meta(getReadableDatabase(),"session"))&&age>=0&&age<TTL;
    }
    String etag(String session){return usable(session)?meta(getReadableDatabase(),"etag"):"";}
    void clear(){
        SQLiteDatabase db=getWritableDatabase();db.beginTransaction();
        try{db.delete("snapshot",null,null);db.delete("metadata",null,null);db.setTransactionSuccessful();}finally{db.endTransaction();}
    }
    void replace(JSONObject data,String session,String etag)throws Exception{
        if(data.getInt("schema")!=1||session.isEmpty())throw new JSONException("Invalid snapshot");
        data.getLong("user_id");
        SQLiteDatabase db=getWritableDatabase();db.beginTransaction();
        try{
            db.delete("snapshot",null,null);db.delete("metadata",null,null);
            for(String section:SECTIONS){
                JSONArray rows=data.getJSONArray(section);
                for(int i=0;i<rows.length();i++){
                    JSONObject row=rows.getJSONObject(i);ContentValues cv=new ContentValues();
                    cv.put("section",section);cv.put("id",row.getLong("id"));cv.put("data",row.toString());
                    db.insertOrThrow("snapshot",null,cv);
                }
            }
            put(db,"session",session);put(db,"etag",etag);put(db,"updated",Long.toString(System.currentTimeMillis()));db.setTransactionSuccessful();
        }finally{db.endTransaction();}
    }
    void touch(String session){if(usable(session))put(getWritableDatabase(),"updated",Long.toString(System.currentTimeMillis()));}
    JSONArray rows(String section)throws JSONException{
        JSONArray rows=new JSONArray();
        try(Cursor c=getReadableDatabase().rawQuery("SELECT data FROM snapshot WHERE section=? ORDER BY id",new String[]{section})){while(c.moveToNext())rows.put(new JSONObject(c.getString(0)));}
        return rows;
    }
}
