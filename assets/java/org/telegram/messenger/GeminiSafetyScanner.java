/*
 * Tiflogram: Gemini API orqali shubhali kanal/guruh/botlarni tekshirish.
 * Model: gemini-3.5-flash-lite (yengil, barqaror, klassifikatsiya uchun)
 */
package org.telegram.messenger;

import android.content.SharedPreferences;
import android.text.TextUtils;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;
import org.telegram.tgnet.TLRPC;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.concurrent.atomic.AtomicBoolean;

public class GeminiSafetyScanner {

    private static final String TAG = "TiflogramGemini";
    // Eng yengil barqaror model (klassifikatsiya / triage uchun)
    public static final String MODEL = "gemini-3.5-flash-lite";
    private static final String API_URL =
            "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent?key=";

    public static final String PREFS = "tiflogram_gemini";
    public static final String KEY_API = "gemini_api_key";
    public static final String KEY_ENABLED = "gemini_scan_enabled";
    public static final String KEY_AUTO_DELETE = "gemini_auto_delete";
    public static final String KEY_LAST_SCAN = "gemini_last_scan_ms";
    public static final long INTERVAL_MS = 24L * 60L * 60L * 1000L;

    private static final AtomicBoolean running = new AtomicBoolean(false);

    public static SharedPreferences prefs() {
        return ApplicationLoader.applicationContext.getSharedPreferences(PREFS, android.content.Context.MODE_PRIVATE);
    }

    public static String getApiKey() {
        return prefs().getString(KEY_API, "");
    }

    public static void setApiKey(String key) {
        prefs().edit().putString(KEY_API, key != null ? key.trim() : "").apply();
    }

    public static boolean isEnabled() {
        return prefs().getBoolean(KEY_ENABLED, false) && !TextUtils.isEmpty(getApiKey());
    }

    public static void setEnabled(boolean v) {
        prefs().edit().putBoolean(KEY_ENABLED, v).apply();
    }

    public static boolean isAutoDelete() {
        return prefs().getBoolean(KEY_AUTO_DELETE, true);
    }

    public static void setAutoDelete(boolean v) {
        prefs().edit().putBoolean(KEY_AUTO_DELETE, v).apply();
    }

    public static void scheduleIfNeeded() {
        if (!isEnabled()) return;
        long last = prefs().getLong(KEY_LAST_SCAN, 0);
        long now = System.currentTimeMillis();
        if (now - last >= INTERVAL_MS) {
            Utilities.globalQueue.postRunnable(() -> runScan(UserConfig.selectedAccount));
        }
    }

    public static void runScan(final int account) {
        if (!isEnabled()) return;
        if (!running.compareAndSet(false, true)) return;
        try {
            doScan(account);
            prefs().edit().putLong(KEY_LAST_SCAN, System.currentTimeMillis()).apply();
        } catch (Exception e) {
            FileLog.e(TAG + " scan error", e);
        } finally {
            running.set(false);
        }
    }

    private static void doScan(int account) throws Exception {
        MessagesController mc = MessagesController.getInstance(account);
        MessagesStorage storage = MessagesStorage.getInstance(account);
        ArrayList<TLRPC.Dialog> dialogs = new ArrayList<>(mc.getAllDialogs());
        ArrayList<Item> candidates = new ArrayList<>();

        for (int i = 0; i < dialogs.size(); i++) {
            TLRPC.Dialog d = dialogs.get(i);
            long did = d.id;
            if (DialogObject.isEncryptedDialog(did)) continue;

            if (DialogObject.isChatDialog(did)) {
                TLRPC.Chat chat = mc.getChat(-did);
                if (chat == null) continue;
                boolean isChannel = ChatObject.isChannel(chat) && !ChatObject.isMegagroup(chat);
                boolean isGroup = ChatObject.isMegagroup(chat) || (!ChatObject.isChannel(chat));
                if (!isChannel && !isGroup) continue;
                String title = chat.title != null ? chat.title : "";
                String uname = chat.username != null ? chat.username : "";
                candidates.add(new Item(did, isChannel ? "channel" : "group", title, uname, ""));
            } else if (DialogObject.isUserDialog(did)) {
                TLRPC.User user = mc.getUser(did);
                if (user == null || !user.bot) continue;
                String name = UserObject.getUserName(user);
                String uname = user.username != null ? user.username : "";
                candidates.add(new Item(did, "bot", name != null ? name : "", uname, ""));
            }
        }

        if (candidates.isEmpty()) {
            FileLog.d(TAG + " no candidates");
            return;
        }

        // Batch by 15 to keep prompts small
        for (int start = 0; start < candidates.size(); start += 15) {
            int end = Math.min(start + 15, candidates.size());
            ArrayList<Item> batch = new ArrayList<>(candidates.subList(start, end));
            ArrayList<Long> suspicious = classifyBatch(batch);
            if (suspicious == null || suspicious.isEmpty()) continue;

            if (!isAutoDelete()) {
                FileLog.d(TAG + " found suspicious but auto-delete off: " + suspicious);
                continue;
            }

            for (int j = 0; j < suspicious.size(); j++) {
                long dialogId = suspicious.get(j);
                try {
                    deleteDialog(account, dialogId);
                    FileLog.d(TAG + " deleted suspicious dialog " + dialogId);
                } catch (Exception e) {
                    FileLog.e(TAG + " delete failed " + dialogId, e);
                }
            }
        }
    }

    private static void deleteDialog(int account, long dialogId) {
        // Dialogni o'chirish / chiqish (MessagesController orqali)
        MessagesController.getInstance(account).deleteDialog(dialogId, 1, false);
    }

    private static ArrayList<Long> classifyBatch(ArrayList<Item> batch) throws Exception {
        String apiKey = getApiKey();
        if (TextUtils.isEmpty(apiKey)) return null;

        StringBuilder list = new StringBuilder();
        for (int i = 0; i < batch.size(); i++) {
            Item it = batch.get(i);
            list.append(i + 1).append(") type=").append(it.type)
                    .append("; title=").append(sanitize(it.title))
                    .append("; username=@").append(sanitize(it.username))
                    .append("; about=").append(sanitize(it.about))
                    .append("\n");
        }

        String prompt = "You are a safety classifier for Telegram chats. "
                + "Mark an item SUSPICIOUS only if it clearly looks like: scam, phishing, malware, fraud, "
                + "fake support, investment scam, adult spam bots, or obvious malware distribution. "
                + "Do NOT mark normal news, communities, or legitimate bots. "
                + "Reply with ONLY a JSON array of 1-based indexes that are suspicious, e.g. [2,5] or [].\n\n"
                + list;

        JSONObject body = new JSONObject();
        JSONArray contents = new JSONArray();
        JSONObject content = new JSONObject();
        JSONArray parts = new JSONArray();
        JSONObject part = new JSONObject();
        part.put("text", prompt);
        parts.put(part);
        content.put("parts", parts);
        contents.put(content);
        body.put("contents", contents);

        JSONObject genConfig = new JSONObject();
        genConfig.put("temperature", 0.1);
        genConfig.put("maxOutputTokens", 256);
        body.put("generationConfig", genConfig);

        String responseText = httpPost(API_URL + apiKey, body.toString());
        if (responseText == null) return null;

        JSONObject resp = new JSONObject(responseText);
        JSONArray candidatesArr = resp.optJSONArray("candidates");
        if (candidatesArr == null || candidatesArr.length() == 0) return null;
        JSONObject c0 = candidatesArr.getJSONObject(0);
        JSONObject contentOut = c0.optJSONObject("content");
        if (contentOut == null) return null;
        JSONArray partsOut = contentOut.optJSONArray("parts");
        if (partsOut == null || partsOut.length() == 0) return null;
        String text = partsOut.getJSONObject(0).optString("text", "");

        ArrayList<Long> result = new ArrayList<>();
        // Extract JSON array from response
        int a = text.indexOf('[');
        int b = text.lastIndexOf(']');
        if (a < 0 || b <= a) return result;
        JSONArray idxs = new JSONArray(text.substring(a, b + 1));
        for (int i = 0; i < idxs.length(); i++) {
            int oneBased = idxs.optInt(i, -1);
            if (oneBased >= 1 && oneBased <= batch.size()) {
                result.add(batch.get(oneBased - 1).dialogId);
            }
        }
        return result;
    }

    private static String httpPost(String urlStr, String json) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(urlStr);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            conn.setDoOutput(true);
            conn.setConnectTimeout(20000);
            conn.setReadTimeout(45000);
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            conn.setFixedLengthStreamingMode(bytes.length);
            OutputStream os = conn.getOutputStream();
            os.write(bytes);
            os.close();
            int code = conn.getResponseCode();
            BufferedReader reader = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? conn.getInputStream() : conn.getErrorStream(),
                    StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) sb.append(line);
            reader.close();
            if (code < 200 || code >= 300) {
                FileLog.e(TAG + " HTTP " + code + " " + sb);
                return null;
            }
            return sb.toString();
        } catch (Exception e) {
            FileLog.e(TAG + " http error", e);
            return null;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    private static String sanitize(String s) {
        if (s == null) return "";
        s = s.replace('\n', ' ').replace('\r', ' ');
        if (s.length() > 120) s = s.substring(0, 120);
        return s;
    }

    private static class Item {
        final long dialogId;
        final String type;
        final String title;
        final String username;
        final String about;

        Item(long dialogId, String type, String title, String username, String about) {
            this.dialogId = dialogId;
            this.type = type;
            this.title = title;
            this.username = username;
            this.about = about;
        }
    }
}
