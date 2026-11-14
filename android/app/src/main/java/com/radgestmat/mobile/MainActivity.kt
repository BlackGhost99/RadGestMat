package com.radgestmat.mobile

import android.app.Activity
import android.app.KeyguardManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.view.WindowManager
import android.widget.*
import org.json.JSONObject
import java.net.*
import java.security.KeyStore
import java.time.Instant
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class MainActivity : Activity() {
    private val base = "https://radgestmat.onrender.com/api/mobile/v1/"
    private val cookies = CookieManager(null, CookiePolicy.ACCEPT_ORIGINAL_SERVER)
    private lateinit var panel: LinearLayout
    private var pending: JSONObject? = null
    private var busy = false
    private var pendingEdit: (() -> Unit)? = null
    private var pendingSync: Pair<JSONObject, org.json.JSONArray>? = null
    private val alias = "radgestmat-cache-v1"
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        loginScreen()
    }
    private fun layout() {
        panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 48, 32, 32)
        }
        setContentView(ScrollView(this).apply { addView(panel) })
    }
    private fun label(value: String) {
        panel.addView(TextView(this).apply { text = value; textSize = 18f; setPadding(0,12,0,12) })
    }
    private fun button(value: String, action: () -> Unit) {
        panel.addView(Button(this).apply { text = value; setOnClickListener { action() } })
    }
    private fun loginScreen() {
        layout()
        label("RadGestMat — Inventaire")
        val username = EditText(this).apply { hint = "Identifiant"; isSingleLine = true }
        val password = EditText(this).apply { hint = "Mot de passe"; inputType = 129 }
        panel.addView(username); panel.addView(password)
        button("Connexion en ligne") {
            val u = username.text.toString()
            val p = password.text.toString()
            password.text.clear()
            if (!getSystemService(KeyguardManager::class.java).isDeviceSecure) {
                label("Configurez le verrouillage sécurisé du téléphone."); return@button
            }
            Thread {
                try {
                    val csrf = request("auth/session/").getString("csrf_token")
                    val session = request("auth/login/", "username="+encode(u)+"&password="+encode(p), csrf)
                    val snapshot = request("bootstrap/")
                    require(snapshot.getLong("account_id") == session.getLong("account_id"))
                    snapshot.put("offline_until", session.getString("offline_until"))
                    runOnUiThread { pending = snapshot; unlock(2) }
                } catch (e: Exception) { runOnUiThread { label("Connexion impossible. Vérifiez le réseau et les identifiants.") } }
            }.start()
        }
        button("Ouvrir hors connexion") { unlock(1) }
    }
    private fun encode(value: String) = URLEncoder.encode(value, "UTF-8")
    private fun request(path: String, body: String? = null, csrf: String? = null, json: Boolean = false): JSONObject {
        val uri = URI.create(base + path)
        val connection = uri.toURL().openConnection() as HttpURLConnection
        connection.instanceFollowRedirects = false
        connection.connectTimeout = 25000; connection.readTimeout = 60000
        try {
            connection.setRequestProperty("Accept", "application/json")
            cookies.get(uri, emptyMap()).forEach { (k,v) -> connection.setRequestProperty(k,v.joinToString("; ")) }
            if (body != null) {
                connection.requestMethod = "POST"; connection.doOutput = true
                connection.setRequestProperty("Content-Type", if (json) "application/json" else "application/x-www-form-urlencoded")
                connection.setRequestProperty("Origin", "https://radgestmat.onrender.com")
                connection.setRequestProperty("X-CSRFToken", csrf ?: "")
                connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            if (connection.responseCode != 200) throw java.io.IOException("HTTP "+connection.responseCode)
            cookies.put(uri, connection.headerFields.filterKeys { it != null })
            return JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
        } finally { connection.disconnect() }
    }
    private fun unlock(code: Int) {
        val manager = getSystemService(KeyguardManager::class.java)
        val intent = manager.createConfirmDeviceCredentialIntent("RadGestMat", "Confirmez votre identité")
        if (intent == null) { label("Verrouillage sécurisé requis."); return }
        startActivityForResult(intent, code)
    }
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode != RESULT_OK) { pending = null; pendingSync = null; pendingEdit = null; busy = false; return }
        if (requestCode == 4) { val action = pendingEdit; pendingEdit = null; action?.invoke(); return }
        if (requestCode == 3) {
            try {
                val (original, results) = requireNotNull(pendingSync)
                val snapshot = JSONObject(original.toString())
                val queue = snapshot.getJSONArray("outbox")
                val rows = snapshot.getJSONArray("materiels")
                for (i in 0 until results.length()) {
                    val result = results.getJSONObject(i)
                    for (j in 0 until rows.length()) {
                        val row = rows.getJSONObject(j)
                        if (row.getLong("id") == result.getLong("id")) row.put("date_modification",result.getString("date_modification"))
                    }
                    queue.remove(0)
                }
                save(snapshot); inventory(snapshot)
                if (queue.length() > 0) label("Opérations restantes conservées : conflit, accès refusé ou réseau indisponible.")
            } catch (e: Exception) { loginScreen(); label("Les opérations locales sont conservées.") }
            finally { pendingSync = null; busy = false }
            return
        }
        try {
            val snapshot = if (requestCode == 2) {
                val value = requireNotNull(pending)
                if (filesDir.resolve("inventory.enc").exists()) {
                    val old = load()
                    if ((old.optJSONArray("outbox")?.length() ?: 0) > 0) {
                        require(old.getLong("account_id") == value.getLong("account_id"))
                        old.put("offline_until", value.getString("offline_until"))
                        save(old); pending = null; old
                    } else { save(value); pending = null; value }
                } else { save(value); pending = null; value }
            } else load()
            require(Instant.now().isBefore(Instant.parse(snapshot.getString("offline_until"))))
            inventory(snapshot)
        } catch (e: Exception) { pending = null; loginScreen(); label("Session locale indisponible ou expirée. Reconnectez-vous.") }
    }
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(alias,null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setUserAuthenticationRequired(true)
                .setUserAuthenticationParameters(30, KeyProperties.AUTH_DEVICE_CREDENTIAL)
                .build())
        }.generateKey()
    }
    private fun save(snapshot: JSONObject) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE,key())
        val bytes = cipher.doFinal(snapshot.toString().toByteArray(Charsets.UTF_8))
        val file = android.util.AtomicFile(filesDir.resolve("inventory.enc"))
        val stream = file.startWrite()
        try { stream.write(cipher.iv + bytes); file.finishWrite(stream) }
        catch (e: Exception) { file.failWrite(stream); throw e }
    }
    private fun load(): JSONObject {
        val bytes = android.util.AtomicFile(filesDir.resolve("inventory.enc")).readFully()
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE,key(),GCMParameterSpec(128,bytes.copyOfRange(0,12)))
        return JSONObject(String(cipher.doFinal(bytes.copyOfRange(12,bytes.size)),Charsets.UTF_8))
    }
    private fun editMaterial(snapshot: JSONObject, row: JSONObject) {
        val queue = snapshot.getJSONArray("outbox")
        for (i in 0 until queue.length()) {
            if (queue.getJSONObject(i).getLong("material_id") == row.getLong("id")) {
                label("Une modification est déjà en attente pour ce matériel."); return
            }
        }
        val name = EditText(this).apply { setText(row.optString("nom")); hint = "Nom" }
        android.app.AlertDialog.Builder(this).setTitle("Modifier le matériel").setView(name)
            .setNegativeButton("Annuler",null).setPositiveButton("Enregistrer") { _,_ ->
                val value = name.text.toString().trim()
                if (value.isNotEmpty() && value.length <= 200) {
                    pendingEdit = {
                        try {
                            val copy = JSONObject(snapshot.toString())
                            val changes = JSONObject().put("nom",value)
                            copy.getJSONArray("outbox").put(JSONObject()
                                .put("operation_id",java.util.UUID.randomUUID().toString())
                                .put("material_id",row.getLong("id"))
                                .put("base_revision",row.getString("date_modification"))
                                .put("changes",changes))
                            val rows = copy.getJSONArray("materiels")
                            for (i in 0 until rows.length()) {
                                val item = rows.getJSONObject(i)
                                if (item.getLong("id") == row.getLong("id")) item.put("nom",value)
                            }
                            save(copy); inventory(copy)
                        } catch (e: Exception) { label("Enregistrement impossible.") }
                    }
                    unlock(4)
                }
            }.show()
    }
    private fun inventory(snapshot: JSONObject) {
        layout()
        val rows = snapshot.getJSONArray("materiels")
        label("Inventaire local — "+rows.length()+" matériels")
        val queue = snapshot.optJSONArray("outbox") ?: org.json.JSONArray().also { snapshot.put("outbox",it) }
        label("Opérations en attente : "+queue.length())
        button("Synchroniser") {
            if (busy) return@button
            busy = true
            Thread {
                try {
                    val session = request("auth/session/")
                    require(session.optBoolean("authenticated") && session.getLong("account_id") == snapshot.getLong("account_id"))
                    val csrf = session.getString("csrf_token")
                    // Keep acknowledgements in memory until authenticated local persistence.
                    val results = org.json.JSONArray()
                    for (i in 0 until queue.length()) {
                        try { results.put(request("material/update/",queue.getJSONObject(i).toString(),csrf,true)) }
                        catch (e: Exception) { break }
                    }
                    runOnUiThread {
                        pendingSync = Pair(snapshot,results)
                        unlock(3)
                    }
                } catch (e: Exception) { runOnUiThread { busy = false; label("Synchronisation impossible. Reconnectez-vous en ligne.") } }
            }.start()
        }
        button("Verrouiller") { if (!busy) loginScreen() }
        val filter = EditText(this).apply { hint = "Rechercher un matériel" }
        panel.addView(filter)
        val results = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        panel.addView(results)
        fun render(query: String) {
            results.removeAllViews()
            for (i in 0 until rows.length()) {
                val row = rows.getJSONObject(i)
                val value = row.optString("nom")+" — "+row.optString("asset_id")+" — "+row.optString("statut_disponibilite")
                if (value.contains(query,ignoreCase=true)) results.addView(TextView(this).apply { text=value; textSize=16f; setPadding(0,14,0,14); setOnClickListener { if (!busy) editMaterial(snapshot,row) } })
            }
        }
        filter.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) { render(s.toString()) }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
        render("")
    }
}
