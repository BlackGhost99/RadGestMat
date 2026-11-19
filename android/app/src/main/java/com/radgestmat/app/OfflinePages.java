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
    static String icon(String name){
        String path;
        switch(name){
            case "home": path="<path d='M3 10 12 3l9 7v11h-6v-7H9v7H3z'/>";break;
            case "box": path="<rect x='3' y='4' width='18' height='16' rx='2'/><path d='M3 9h18M9 4v5'/>";break;
            case "plus": path="<circle cx='12' cy='12' r='9'/><path d='M12 8v8M8 12h8'/>";break;
            case "arrows": path="<path d='M3 7h17l-4-4m4 4-4 4M21 17H4l4-4m-4 4 4 4'/>";break;
            case "bell": path="<path d='M18 8a6 6 0 0 0-12 0c0 7-3 7-3 10h18c0-3-3-3-3-10M10 21h4'/>";break;
            case "menu": path="<path d='M4 6h16M4 12h16M4 18h16'/>";break;
            case "scan": path="<path d='M3 8V3h5m8 0h5v5m0 8v5h-5m-8 0H3v-5M7 7h3v3H7zm7 0h3v3h-3zm-7 7h3v3H7zm7 0h3v3h-3z'/>";break;
            case "check": path="<circle cx='12' cy='12' r='9'/><path d='m8 12 3 3 5-6'/>";break;
            case "tools": path="<path d='m14 6 4-4 4 4-4 4-3-1L5 21l-3-3L14 6z'/>";break;
            case "people": path="<circle cx='9' cy='8' r='3'/><path d='M2 20v-3a7 7 0 0 1 14 0v3M17 5a3 3 0 0 1 0 6m1 3c3 1 4 3 4 6'/>";break;
            case "alert": path="<path d='m12 3 10 18H2zM12 9v5m0 3v1'/>";break;
            case "clock": path="<circle cx='12' cy='12' r='9'/><path d='M12 6v6l4 2'/>";break;
            case "tag": path="<path d='M3 3h9l9 9-9 9-9-9zM7 7h.01'/>";break;
            case "search": path="<circle cx='10' cy='10' r='6'/><path d='m15 15 6 6'/>";break;
            case "chevron": path="<path d='m9 5 7 7-7 7'/>";break;
            case "settings": path="<circle cx='12' cy='12' r='4'/><path d='M12 2v4m0 12v4M2 12h4m12 0h4M5 5l3 3m8 8 3 3M19 5l-3 3m-8 8-3 3'/>";break;
            case "logout": path="<path d='M10 3H4v18h6m5-15 6 6-6 6m-7-6h13'/>";break;
            default:path="<circle cx='12' cy='12' r='9'/>";
        }
        return "<svg viewBox='0 0 24 24' aria-hidden='true'>"+path+"</svg>";
    }
    static String iconLink(String path,String label,String image,String cls){
        return "<a class='"+cls+"' href='"+esc(path)+"'>"+icon(image)+"<span>"+esc(label)+"</span></a>";
    }
    static String metric(String path,String label,int value,String image,String type){
        return "<a class='metric article "+type+"' href='"+esc(path)+"'>"+icon(image)+"<b>"+value+"</b><span>"+esc(label)+"</span></a>";
    }
    static String statusLabel(String s){
        switch(s){case "DISPONIBLE":return "Disponible";case "ATTRIBUE":return "Attribué";case "EN_MAINTENANCE":case "MAINTENANCE":return "Maintenance";case "HORS_SERVICE":return "Hors service";case "DEFECTUEUX":return "Défectueux";default:return s.replace('_',' ');}
    }
    static String badge(String s){String tone=s.equals("DISPONIBLE")?"good":s.equals("HORS_SERVICE")||s.equals("DEFECTUEUX")?"danger":"warn";return "<span class='badge "+tone+"'>"+esc(statusLabel(s))+"</span>";}
    static java.time.Instant due(JSONObject o){try{return java.time.OffsetDateTime.parse(field(o,"deadline")).toInstant();}catch(Exception e){return null;}}
    static String options(Set<String> values,boolean status){StringBuilder b=new StringBuilder();for(String v:values)if(!v.isEmpty())b.append("<option value='").append(esc(v)).append("'>").append(esc(status?statusLabel(v):v)).append("</option>");return b.toString();}
    static WebResourceResponse serve(Context context,Uri uri){
        if(uri.getQuery()!=null)return null;
        String path=uri.getPath();
        if(path==null||!(Arrays.asList("/","/materiel/","/attributions/","/clients/","/categories/","/alertes/","/notifications/dashboard/").contains(path)||path.matches("/materiel/[0-9]+/")||path.matches("/scan/OKP-[0-9]+/")))return null;
        try(OfflineStore store=new OfflineStore(context)){
            String session=OfflineStore.session();if(!store.usable(session))return null;
            String title="Accueil";StringBuilder body=new StringBuilder();
            JSONArray materials=store.rows("materials"),loans=store.rows("loans");
            int reminders=0,overdue=0,allOverdue=0;Set<String> reminderKeys=new HashSet<>();
            for(int i=0;i<loans.length();i++){
                JSONObject o=loans.getJSONObject(i);
                java.time.Instant deadlineInstant=due(o);if(deadlineInstant!=null&&deadlineInstant.isBefore(java.time.Instant.now()))allOverdue++;
                if(o.optBoolean("personal")&&o.optString("type").equals("TEMPORAIRE")&&!field(o,"deadline").isEmpty()&&reminderKeys.add(field(o,"materiel_id")+"|"+field(o,"deadline"))){
                    try{java.time.Instant due=java.time.OffsetDateTime.parse(field(o,"deadline")).toInstant();if(due.isBefore(java.time.Instant.now().plusSeconds(7200)))reminders++;if(due.isBefore(java.time.Instant.now()))overdue++;}catch(Exception ignored){}
                }
            }
            if(path.equals("/")){
                title="Vue d’ensemble";
                int available=0,assigned=0,maintenance=0,defective=0,unavailable=0;
                for(int i=0;i<materials.length();i++){
                    JSONObject o=materials.getJSONObject(i);String status=field(o,"statut_disponibilite"),state=field(o,"etat_technique");
                    if(status.equals("DISPONIBLE"))available++;
                    if(status.equals("ATTRIBUE"))assigned++;
                    if(status.contains("MAINTENANCE")||state.contains("MAINTENANCE"))maintenance++;
                    if(status.equals("HORS_SERVICE"))unavailable++;
                    if(state.contains("DEFECT")||status.equals("DEFECTUEUX"))defective++;
                }
                int rate=materials.length()==0?0:(int)Math.round(100.0*available/materials.length());
                body.append("<a class='hero' href='/materiel/'><div>Parc informatique<strong>").append(materials.length()).append("</strong><small>Équipements au total</small></div><div class='rate'><strong>").append(rate).append("%</strong><small>Disponibles</small><progress max='100' value='").append(rate).append("'></progress></div></a>");
                body.append("<h2>Indicateurs</h2><div class='tiles'>")
                    .append(metric("/materiel/","Disponibles",available,"check","good"))
                    .append(metric("/attributions/","Attribués",assigned,"arrows",""))
                    .append(metric("/materiel/","Maintenance",maintenance,"tools","warn"))
                    .append(metric("/materiel/","Défectueux",defective,"tools","danger"))
                    .append(metric("/materiel/","Hors service",unavailable,"alert","danger"))
                    .append(metric("/clients/","Clients",store.rows("clients").length(),"people",""))
                    .append(metric("/alertes/","Alertes",store.rows("alerts").length(),"alert","danger"))
                    .append(metric("/attributions/","Retards",allOverdue,"clock","warn"))
                    .append(metric("/attributions/","Attributions",loans.length(),"arrows","")).append("</div>");
                body.append("<h2>Actions rapides</h2><div class='actions'>")
                    .append(iconLink("/materiel/ajouter/","Ajouter","plus",""))
                    .append(iconLink("/materiel/","Recherche","search",""))
                    .append(iconLink("/scan/","Scanner","scan",""))
                    .append(iconLink("/categories/","Catégories","tag","")).append("</div>");
            }else if(path.equals("/materiel/")){
                title="Inventaire";
                Map<String,List<JSONObject>> groups=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
                Set<String> statuses=new TreeSet<>(),departments=new TreeSet<>();
                for(int i=0;i<materials.length();i++){JSONObject o=materials.getJSONObject(i);String name=field(o,"nom");groups.computeIfAbsent(name,k->new ArrayList<>()).add(o);statuses.add(field(o,"statut_disponibilite"));departments.add(field(o,"departement__nom"));}
                body.append("<div class='toolbar'><span class='muted'>").append(materials.length()).append(" équipements · ").append(groups.size()).append(" groupes</span>").append(iconLink("/materiel/ajouter/","Ajouter","plus","primary")).append("</div>");
                body.append("<div class='filters'><select id='status' aria-label='Statut'><option value=''>Tous les statuts</option>").append(options(statuses,true)).append("</select><select id='department' aria-label='Département'><option value=''>Tous les départements</option>").append(options(departments,false)).append("</select></div>");
                for(Map.Entry<String,List<JSONObject>> entry:groups.entrySet()){
                    int available=0;for(JSONObject o:entry.getValue())if(field(o,"statut_disponibilite").equals("DISPONIBLE"))available++;
                    body.append("<article class='group' data-group><details><summary><span class='group-icon'>").append(icon("box")).append("</span><div class='group-copy'><strong>").append(esc(entry.getKey())).append("</strong><small>").append(entry.getValue().size()).append(" équipement(s) · ").append(available).append(" disponible(s)</small></div><span class='chevron'>").append(icon("chevron")).append("</span></summary><div class='group-list'>");
                    for(JSONObject o:entry.getValue()){
                        body.append("<a class='item' data-row data-status='").append(esc(field(o,"statut_disponibilite"))).append("' data-dept='").append(esc(field(o,"departement__nom"))).append("' href='/materiel/").append(o.getLong("id")).append("/'><div class='item-top'><strong>").append(esc(field(o,"asset_id"))).append("</strong>").append(badge(field(o,"statut_disponibilite"))).append("</div><small>").append(line(o,"nom","categorie__nom","departement__nom","location","marque","modele")).append("</small></a>");
                    }
                    body.append("</div></details></article>");
                }
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
            String html="<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><style>"+":root{color-scheme:light;--bg:#edf2f8;--card:#fff;--ink:#172c45;--muted:#61738a;--blue:#2169bc;--line:#dce5ef;--shadow:0 3px 12px #173d6810}*{box-sizing:border-box}body{margin:0;font:14px system-ui,sans-serif;background:var(--bg);color:var(--ink);padding-bottom:88px}a{color:var(--blue);text-decoration:none}button,input,select{font:inherit}header{position:sticky;top:0;z-index:10;background:linear-gradient(110deg,#102b4d,#205b99);color:white;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;min-height:58px;box-shadow:0 3px 12px #102b4d22}header strong{display:flex;gap:9px;align-items:center;font-size:18px}header a,header button{color:white}header button{border:0;background:transparent;padding:8px}svg{width:21px;height:21px;vertical-align:middle;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.brand{display:grid;place-items:center;background:#ffffff24;border-radius:9px;width:34px;height:34px}.head-actions{display:flex;align-items:center;gap:8px}.bell{position:relative;display:inline-flex;padding:8px}.count{position:absolute;top:0;right:-3px;font-size:10px;background:#ffcc55;color:#362600;border-radius:12px;padding:2px 5px}.late{background:#dc3545;color:white}main{max-width:900px;margin:auto;padding:16px 13px}h1{font-size:23px;margin:0 0 7px;letter-spacing:-.5px}h2{font-size:16px;margin:19px 0 10px}aside{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:11px;color:var(--muted);margin:0 0 16px}aside a{font-weight:600}.sync-dot{display:inline-block;background:#249477;width:7px;height:7px;border-radius:50%;margin-right:5px}article{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:13px;margin:8px 0;box-shadow:var(--shadow);overflow-wrap:anywhere}article strong{font-size:15px}small{display:block;color:var(--muted);font-size:12px;margin-top:5px;line-height:1.5}.hero{color:white;background:linear-gradient(120deg,#14395e,#2675ba);border-radius:17px;padding:19px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 6px 20px #15497b25}.hero strong{display:block;font-size:36px;line-height:1.15;margin:5px 0}.hero small{color:#d8e6f4}.rate{text-align:right;min-width:92px}.rate strong{font-size:25px}.rate progress{width:86px;height:7px;accent-color:#8de4c9}.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.metric{display:flex;flex-direction:column;gap:4px;margin:0;padding:12px 9px;border-radius:13px}.metric svg{color:var(--blue)}.metric b{font-size:24px;line-height:1.25}.metric span{font-size:11px;color:var(--muted)}.metric.good svg{color:#16835c}.metric.warn svg{color:#bd780c}.metric.danger svg{color:#bb3348}.actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.actions a{display:flex;flex-direction:column;align-items:center;gap:7px;background:var(--card);border:1px solid var(--line);padding:12px 3px;border-radius:12px;font-size:11px;font-weight:600;text-align:center}.search{display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:0 12px;margin-bottom:10px;color:var(--muted)}.search input{background:transparent;color:var(--ink);border:0;min-width:0;width:100%;padding:13px 0;outline:none}.filters{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:10px}.filters select{min-width:0;width:100%;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:10px;border-radius:9px}.primary{display:inline-flex;align-items:center;gap:7px;color:#fff;background:linear-gradient(100deg,#2169bc,#309ad9);border-radius:10px;padding:10px 13px;font-size:13px;font-weight:600}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:12px 0}.muted{color:var(--muted);font-size:12px}.badge{display:inline-block;font-size:10px;font-weight:650;padding:4px 7px;border-radius:7px;background:#e6eef8;color:#27609d}.badge.good{background:#dff3e9;color:#166846}.badge.warn{background:#fff0d2;color:#8a5600}.badge.danger{background:#fbe3e7;color:#9f2639}.group{padding:0;overflow:hidden}.group summary{list-style:none;display:flex;align-items:center;gap:10px;padding:12px;cursor:pointer}.group summary::-webkit-details-marker{display:none}.group[open] .chevron{transform:rotate(90deg)}.group .chevron{margin-left:auto;width:17px}.group-icon{display:grid;place-items:center;flex-shrink:0;width:38px;height:38px;background:#e7f0fc;color:#2169bc;border-radius:11px}.group-copy{min-width:0;flex:1}.group-copy strong{display:block}.group-copy small{margin-top:3px}.group-list{border-top:1px solid var(--line)}.item{display:block;padding:10px 12px;border-bottom:1px solid var(--line)}.item:last-child{border:0}.item-top{display:flex;justify-content:space-between;align-items:center;gap:8px}.item-top strong{font-size:13px}.empty{text-align:center;color:var(--muted);padding:26px 10px}.nav{position:fixed;bottom:0;left:0;right:0;z-index:12;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));background:var(--card);border-top:1px solid var(--line);padding:7px 3px;box-shadow:0 -3px 14px #12304912}.nav a{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:4px 0;font-size:10px;font-weight:600;color:var(--muted);min-width:0;white-space:nowrap}.nav a.active{color:var(--blue)}.nav a.active svg{background:#e5effd;border-radius:7px;box-shadow:0 0 0 4px #e5effd}.menu{display:none;position:fixed;z-index:30;top:0;bottom:0;left:0;width:min(85vw,340px);background:var(--card);padding:18px;box-shadow:0 0 0 100vmax #10243f66;overflow:auto}.menu.open{display:block}.menu h2{margin:0}.menu a{display:flex;align-items:center;gap:10px;padding:13px 5px;border-bottom:1px solid var(--line);font-size:14px}.menu button{float:right;border:0;background:transparent;color:var(--ink)}[hidden]{display:none!important}@media(prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#101a28;--card:#1b293b;--ink:#e4ecf7;--muted:#a5b6cb;--blue:#81b8fc;--line:#304158;--shadow:none}.group-icon,.nav a.active svg{background:#294365;color:#a7ceff;box-shadow:none}.badge{background:#304b70;color:#d8e9ff}}.article{background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow);color:var(--ink)}"+"</style></head><body>"+
                "<header><strong><span class='brand'>"+icon("box")+"</span>RadGestMat</strong><div class='head-actions'><a class='bell' href='/notifications/dashboard/' aria-label='Notifications'>"+icon("bell")+(reminders>0?"<span class='count "+(overdue>0?"late":"")+"'>"+reminders+"</span>":"")+"</a><button id='menu-open' aria-label='Menu' aria-expanded='false'>"+icon("menu")+"</button></div></header>"+
                "<section class='menu' id='menu'><button id='menu-close' aria-label='Fermer le menu'>✕</button><h2>Navigation</h2>"+iconLink("/clients/","Clients","people","")+iconLink("/categories/","Catégories","tag","")+iconLink("/alertes/","Alertes","alert","")+iconLink("/notifications/preferences/","Paramètres de notifications","settings","")+iconLink("/users/settings/","Mon compte","settings","")+iconLink("/users/utilisateurs/","Gestion des utilisateurs (administrateurs)","people","")+iconLink("/logout/","Déconnexion en ligne","logout","")+"</section>"+
                "<main><h1>"+esc(title)+"</h1><aside><span><span class='sync-dot'></span>Local · "+esc(updated)+"</span>"+link(path+"?online=1","Vue complète")+"</aside>"+
                (path.equals("/")?"":"<div class='search'>"+icon("search")+"<input type='search' id='search' placeholder='Rechercher…' aria-label='Rechercher'></div>")+body+"</main><nav class='nav'>"+
                iconLink("/","Accueil","home",path.equals("/")?"active":"")+
                iconLink("/materiel/","Inventaire","box",path.startsWith("/materiel/")?"active":"")+
                iconLink("/scan/","Scanner","scan",path.startsWith("/scan/")?"active":"")+
                iconLink("/attributions/","Attributions","arrows",path.equals("/attributions/")?"active":"")+
                iconLink("/alertes/","Alertes","alert",path.equals("/alertes/")?"active":"")+
                "</nav><script>"+"(()=>{const q=document.getElementById('search'),status=document.getElementById('status'),dept=document.getElementById('department');function norm(t){return t.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase()}function filter(){let term=norm(q?q.value:''),st=status?status.value:'',dp=dept?dept.value:'';document.querySelectorAll('[data-row]').forEach(r=>{r.hidden=!(norm(r.textContent).includes(term)&&(!st||r.dataset.status===st)&&(!dp||r.dataset.dept===dp))});document.querySelectorAll('[data-group]').forEach(g=>{g.hidden=!g.querySelector('[data-row]:not([hidden])');if(term||st||dp)g.querySelector('details').open=!g.hidden})}if(q)q.addEventListener('input',filter);if(status)status.addEventListener('change',filter);if(dept)dept.addEventListener('change',filter);let menu=document.getElementById('menu');document.getElementById('menu-open').onclick=()=>{menu.classList.add('open');document.getElementById('menu-open').setAttribute('aria-expanded','true')};document.getElementById('menu-close').onclick=()=>{menu.classList.remove('open');document.getElementById('menu-open').setAttribute('aria-expanded','false')};})();"+"</script></body></html>";
            HashMap<String,String> headers=new HashMap<>();headers.put("Cache-Control","no-store");headers.put("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'");
            return new WebResourceResponse("text/html","UTF-8",200,"OK",headers,new ByteArrayInputStream(html.getBytes(StandardCharsets.UTF_8)));
        }catch(Exception e){return null;}
    }
}
