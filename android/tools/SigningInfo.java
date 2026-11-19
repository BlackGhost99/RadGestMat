import java.io.File;
import java.security.KeyStore;
import java.util.ArrayList;

public class SigningInfo {
    public static void main(String[] args) throws Exception {
        char[] password = System.getenv("SIGNING_PASSWORD").toCharArray();
        KeyStore store = KeyStore.getInstance(new File(args[0]), password);
        var entries = new ArrayList<String>();
        var aliases = store.aliases();
        while (aliases.hasMoreElements()) {
            String alias = aliases.nextElement();
            if (store.isKeyEntry(alias)) entries.add(alias);
        }
        String alias = System.getenv("SIGNING_ALIAS");
        if (alias == null || alias.isBlank() || alias.equalsIgnoreCase("AUTO")) {
            if (entries.size() != 1) throw new IllegalStateException("Expected exactly one signing key");
            alias = entries.get(0);
        }
        if (!store.isKeyEntry(alias) || alias.contains("\n") || alias.contains("\r"))
            throw new IllegalStateException("Invalid signing alias");
        char[] keyPassword = System.getenv("SIGNING_KEY_PASSWORD").toCharArray();
        if (!(store.getKey(alias, keyPassword) instanceof java.security.PrivateKey))
            throw new IllegalStateException("Not a private signing key");
        System.out.println("RADGESTMAT_STORE_TYPE=" + store.getType());
        System.out.println("RADGESTMAT_RESOLVED_ALIAS=" + alias);
    }
}
