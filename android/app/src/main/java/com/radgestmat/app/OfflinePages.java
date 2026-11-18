package com.radgestmat.app;
import android.content.Context;
import android.net.Uri;
import android.text.TextUtils;
import android.webkit.WebResourceResponse;
import org.json.*;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;

final class OfflinePages {
    static String esc(String s){return TextUtils.htmlEncode(s==null?"":s);}
    static String field(JSONObject o,String k){return o.isNull(k)?"":o.optString(k,"");}
    static String line(JSONObject o,String... keys){
        StringBuilder b=new StringBuilder();for(String k:keys){String s=field(o,k);if(!s.isEmpty()){if(b.length()>0)b.append(" · ");b.append(s);}}return esc(b.toString());
    }
    static String link(String path,String label){return "<a href='"+esc(path)+"'>"+esc(label)+"</a>";}
    static void card(StringBuilder b,String title,String details,String url){
        b.append("<article data-row><strong>").append(url==null?esc(title):link(url,title)).append("</strong><small>").append(details).append("</small></article>");
    }
    static WebResourceResponse serve(Context context,Uri uri){
        if(uri.getQuery()!=null)return null;
        String path=uri.getPath();
        if(path==null||!(Arrays.asList("/","/materiel/","/attributions/","/clients/","/categories/","/alertes/","/notifications/dashboard/").contains(path)||path.matches("/materiel/[0-9]+/")||path.matches("/scan/OKP-[0-9]+/")))return null;
        try(OfflineStore store=new OfflineStore(context)){
            String session=OfflineStore.session();if(!store.usable(session))return null;
            String title="Accueil";StringBuilder body=new StringBuilder();
            JSONArray materials=store.rows("materials"),loans=store.rows("loans");
            int reminders=0,overdue=0;
            for(int i=0;i<loans.length();i++){
                JSONObject o=loans.getJSONObject(i);
                if(o.optBoolean("personal")&&o.optString("type").equals("TEMPORAIRE")&&!field(o,"deadline").isEmpty()){
                    try{java.time.Instant due=java.time.OffsetDateTime.parse(field(o,"deadline")).toInstant();if(due.isBefore(java.time.Instant.now().plusSeconds(7200)))reminders++;if(due.isBefore(java.time.Instant.now()))overdue++;}catch(Exception ignored){}
                }
            }
            if(path.equals("/")){
                int available=0,assigned=0,maintenance=0;
                for(int i=0;i<materials.length();i++){String status=field(materials.getJSONObject(i),"statut_disponibilite");if(status.equals("DISPONIBLE"))available++;if(status.equals("ATTRIBUE"))assigned++;if(status.equals("MAINTENANCE"))maintenance++;}
                body.append("<div class='tiles'><article><b>").append(materials.length()).append("</b>Total</article><article><b>").append(available).append("</b>Disponible</article><article><b>").append(assigned).append("</b>Attribué</article><article><b>").append(maintenance).append("</b>Maintenance</article></div>");
                body.append("<article>").append(link("/attributions/",loans.length()+" attributions actives")).append("</article>");
            }else if(path.equals("/materiel/")){
                title="Inventaire";body.append("<p>").append(link("/materiel/ajouter/","＋ Ajouter du matériel")).append("</p>");
                for(int i=0;i<materials.length();i++){JSONObject o=materials.getJSONObject(i);card(body,field(o,"nom"),line(o,"asset_id","categorie__nom","departement__nom","statut_disponibilite"),"/materiel/"+o.getLong("id")+"/");}
            }else if(path.startsWith("/materiel/")||path.startsWith("/scan/")){
                title="Matériel";String key=path.split("/")[2];boolean found=false;
                for(int i=0;i<materials.length();i++){
                    JSONObject o=materials.getJSONObject(i);if(!key.equals(field(o,"asset_id"))&&!key.equals(Long.toString(o.getLong("id"))))continue;
                    found=true;card(body,field(o,"nom"),line(o,"asset_id","numero_inventaire","marque","modele","categorie__nom","departement__nom","location","etat_technique","statut_disponibilite"),null);
                    String asset=field(o,"asset_id");if(asset.matches("OKP-[0-9]+"))body.append("<p>").append(link("/materiel/"+asset+"/checkout/","Attribuer (en ligne)")).append(" · ").append(link("/materiel/"+asset+"/checkin/","Restituer (en ligne)")).append("</p>");break;
                }if(!found)return null;
            }else if(path.equals("/attributions/")||path.equals("/notifications/dashboard/")){
                boolean personal=path.startsWith("/notifications/");title=personal?"Notifications":"Attributions actives";
                if(personal)body.append("<p>").append(link("/notifications/preferences/","⚙ Paramètres")).append("</p>");
                Set<String> seen=new HashSet<>();
                for(int i=0;i<loans.length();i++){
                    JSONObject o=loans.getJSONObject(i);String deadline=field(o,"deadline"),label="";
                    if(personal&&(!o.optBoolean("personal")||deadline.isEmpty()||!field(o,"type").equals("TEMPORAIRE")))continue;
                    if(personal&&!seen.add(field(o,"materiel_id")+"|"+deadline))continue;
                    if(!deadline.isEmpty())try{
                        java.time.OffsetDateTime dt=java.time.OffsetDateTime.parse(deadline);
                        if(personal&&dt.toInstant().isAfter(java.time.Instant.now().plusSeconds(172800)))continue;
                        label=dt.toInstant().isBefore(java.time.Instant.now())?"En retard · ":"Retour prévu · ";
                        deadline=dt.atZoneSameInstant(java.time.ZoneId.systemDefault()).format(java.time.format.DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"));
                    }catch(Exception ignored){}
                    card(body,field(o,"nom"),line(o,"asset_id","destination")+" · "+esc(label+deadline),"/materiel/"+o.getLong("materiel_id")+"/");
                }
            }else{
                String section=path.equals("/clients/")?"clients":path.equals("/categories/")?"categories":"alerts";title=section.equals("clients")?"Clients":section.equals("categories")?"Catégories":"Alertes";
                JSONArray rows=store.rows(section);for(int i=0;i<rows.length();i++){JSONObject o=rows.getJSONObject(i);card(body,section.equals("alerts")?field(o,"type_alerte"):field(o,"nom"),line(o,"type_client","severite","materiel__asset_id","departement__nom"),path+o.getLong("id")+"/");}
            }
            if(!session.equals(OfflineStore.session()))return null;
            String updated=new java.text.SimpleDateFormat("dd/MM/yyyy HH:mm",java.util.Locale.FRANCE).format(new java.util.Date(store.updated()));
            String html="<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><meta name='color-scheme' content='light dark'><style>"+
                "*{box-sizing:border-box}body{margin:0;font:16px system-ui;background:#f3f5fa;color:#172535;padding-bottom:78px}header{background:#1759b5;color:white;padding:14px;display:flex;justify-content:space-between;align-items:center;gap:8px}header a{color:white;font-size:20px}main{padding:12px}h1{font-size:23px;margin:8px 0}a{color:#125dbd;text-decoration:none}article{background:white;border-radius:10px;padding:12px;margin:6px 0;overflow-wrap:anywhere}small{display:block;color:#596777;font-size:13px;margin-top:5px}.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:5px}.tiles b{display:block;font-size:25px;color:#1768ca}nav{position:fixed;bottom:0;left:0;right:0;display:flex;justify-content:space-around;gap:3px;background:white;border-top:1px solid #ddd;padding:13px 4px}nav a{font-size:12px;text-align:center}input{width:100%;padding:11px;border:1px solid #bbb;border-radius:8px;font:inherit}aside{font-size:12px;color:#556575;display:flex;justify-content:space-between;gap:8px;margin:8px 0}details a{display:block;padding:6px}.count{font-size:12px;background:#b45309;color:white;border-radius:10px;padding:2px 5px}.late{background:#dc2626}@media(prefers-color-scheme:dark){body{background:#121820;color:#e9edf3}article,nav{background:#202936}small,aside{color:#b4c0ce}a{color:#87bbff}}"+
                "</style></head><body><header><strong>▣ RadGestMat</strong><a href='/notifications/dashboard/' aria-label='Notifications personnelles'>🔔"+(reminders>0?"<span class='count "+(overdue>0?"late":"")+"'>"+reminders+"</span>":"")+"</a></header><main><h1>"+esc(title)+"</h1><aside><span>Copie locale · "+esc(updated)+"</span>"+link(path+"?online=1","Version complète en ligne")+"</aside><input type='search' id='search' placeholder='Rechercher…' aria-label='Rechercher'><details><summary>Menu</summary>"+link("/clients/","Clients")+link("/categories/","Catégories")+link("/alertes/","⚠ Alertes")+link("/notifications/preferences/","Paramètres de notifications")+link("/logout/","Déconnexion en ligne")+"</details>"+body+"</main><nav>"+link("/","Accueil")+link("/materiel/","Inventaire")+link("/materiel/ajouter/","＋ Matériel")+link("/attributions/","Attributions")+link("/notifications/dashboard/","Notifications")+"</nav><script>document.getElementById('search').addEventListener('input',function(){var q=this.value.toLowerCase();document.querySelectorAll('[data-row]').forEach(function(r){r.hidden=!r.textContent.toLowerCase().includes(q)})})</script></body></html>";
            HashMap<String,String> headers=new HashMap<>();headers.put("Cache-Control","no-store");headers.put("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'");
            return new WebResourceResponse("text/html","UTF-8",200,"OK",headers,new ByteArrayInputStream(html.getBytes(StandardCharsets.UTF_8)));
        }catch(Exception e){return null;}
    }
}
