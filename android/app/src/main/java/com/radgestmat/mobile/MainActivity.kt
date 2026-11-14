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
    private fun request(path: String, body: String? = null, csrf: String? = null): JSONObject {
        val uri = URI.create(base + path)
        val connection = uri.toURL().openConnection() as HttpURLConnection
        connection.instanceFollowRedirects = false
        connection.connectTimeout = 25000; connection.readTimeout = 60000
        try {
            connection.setRequestProperty("Accept", "application/json")
            cookies.get(uri, emptyMap()).forEach { (k,v) -> connection.setRequestProperty(k,v.joinToString("; ")) }
            if (body != null) {
                connection.requestMethod = "POST"; connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
                connection.setRequestProperty("Origin", "https://radgestmat.onrender.com")
                connection.setRequestProperty("X-CSRFToken", csrf ?: "")
                connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            require(connection.responseCode == 200)
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
        if (resultCode != RESULT_OK) { pending = null; return }
        try {
            val snapshot = if (requestCode == 2) {
                val value = requireNotNull(pending); save(value); pending = null; value
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
    private fun inventory(snapshot: JSONObject) {
        layout()
        val rows = snapshot.getJSONArray("materiels")
        label("Inventaire local — "+rows.length()+" matériels")
        label("Copie locale en lecture seule")
        button("Verrouiller") { loginScreen() }
        val filter = EditText(this).apply { hint = "Rechercher un matériel" }
        panel.addView(filter)
        val results = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        panel.addView(results)
        fun render(query: String) {
            results.removeAllViews()
            for (i in 0 until rows.length()) {
                val row = rows.getJSONObject(i)
                val value = row.optString("nom")+" — "+row.optString("asset_id")+" — "+row.optString("statut_disponibilite")
                if (value.contains(query,ignoreCase=true)) results.addView(TextView(this).apply { text=value; textSize=16f; setPadding(0,14,0,14) })
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
