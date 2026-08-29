#!/usr/bin/env python3
"""
Tiflogram: Gemini API (gemini-3.5-flash-lite) shubhali kanal/guruh/bot skaneri.
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": 1,
        "label": "ApplicationLoader: Gemini skaner schedule",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java",
        "old": '''        BillingController.getInstance().startConnection();
    }''',
        "new": '''        BillingController.getInstance().startConnection();
        // Tiflogram: Gemini safety scanner (har 24 soat)
        try {
            GeminiSafetyScanner.scheduleIfNeeded();
        } catch (Throwable ignore) {
        }
    }''',
    },
    {
        "id": 2,
        "label": "PrivacySettingsActivity: Gemini maydonlari",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/PrivacySettingsActivity.java",
        "old": '''    private int secretDetailRow;
    private int rowCount;''',
        "new": '''    private int secretDetailRow;
    private int geminiSectionRow;
    private int geminiApiRow;
    private int geminiEnableRow;
    private int geminiAutoDeleteRow;
    private int geminiScanNowRow;
    private int geminiDetailRow;
    private int rowCount;''',
    },
    {
        "id": 3,
        "label": "PrivacySettingsActivity: updateRows Gemini",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/PrivacySettingsActivity.java",
        "old": '''        sessionsRow = rowCount++;
        sessionsDetailRow = rowCount++;

        privacySectionRow = rowCount++;''',
        "new": '''        sessionsRow = rowCount++;
        sessionsDetailRow = rowCount++;

        geminiSectionRow = rowCount++;
        geminiApiRow = rowCount++;
        geminiEnableRow = rowCount++;
        geminiAutoDeleteRow = rowCount++;
        geminiScanNowRow = rowCount++;
        geminiDetailRow = rowCount++;

        privacySectionRow = rowCount++;''',
    },
    {
        "id": 4,
        "label": "PrivacySettingsActivity: isEnabled Gemini",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/PrivacySettingsActivity.java",
        "old": '''                    position == contactsSuggestRow || position == autoDeleteMesages || position == botsBiometryRow;
        }''',
        "new": '''                    position == contactsSuggestRow || position == autoDeleteMesages || position == botsBiometryRow ||
                    position == geminiApiRow || position == geminiEnableRow || position == geminiAutoDeleteRow || position == geminiScanNowRow;
        }''',
    },
    {
        "id": 5,
        "label": "PrivacySettingsActivity: getItemViewType Gemini",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/PrivacySettingsActivity.java",
        "old": '''            } else if (position == privacyShadowRow || position == deleteAccountDetailRow || position == groupsDetailRow || position == sessionsDetailRow || position == secretDetailRow || position == botsDetailRow || position == contactsDetailRow || position == newChatsSectionRow) {
                return 1;
            } else if (position == securitySectionRow || position == advancedSectionRow || position == privacySectionRow || position == secretSectionRow || position == botsSectionRow || position == contactsSectionRow || position == newChatsHeaderRow) {
                return 2;
            } else if (position == secretWebpageRow || position == contactsSyncRow || position == contactsSuggestRow || position == newChatsRow) {
                return 3;''',
        "new": '''            } else if (position == privacyShadowRow || position == deleteAccountDetailRow || position == groupsDetailRow || position == sessionsDetailRow || position == secretDetailRow || position == botsDetailRow || position == contactsDetailRow || position == newChatsSectionRow || position == geminiDetailRow) {
                return 1;
            } else if (position == securitySectionRow || position == advancedSectionRow || position == privacySectionRow || position == secretSectionRow || position == botsSectionRow || position == contactsSectionRow || position == newChatsHeaderRow || position == geminiSectionRow) {
                return 2;
            } else if (position == secretWebpageRow || position == contactsSyncRow || position == contactsSuggestRow || position == newChatsRow || position == geminiEnableRow || position == geminiAutoDeleteRow) {
                return 3;
            } else if (position == geminiApiRow || position == geminiScanNowRow) {
                return 0;''',
    },
]


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (Gemini scanner) ===\n")
    results = []
    file_cache = {}
    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]
        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi")
            results.append(False)
            continue
        if fix["old"] not in content:
            print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
            results.append(False)
            continue
        print(f"✅ [{fix['id']}] {fix['label']}")
        results.append(True)

    failed = results.count(False)
    print(f"\nOK: {len(results)-failed}/{len(results)}")
    if MODE == "check":
        sys.exit(1 if failed else 0)
    if failed:
        sys.exit(1)

    modified = dict(file_cache)
    for fix in FIXES:
        modified[fix["path"]] = modified[fix["path"]].replace(fix["old"], fix["new"], 1)

    # onBind: header + check + settings + detail - inject via additional replace
    path = "TMessagesProj/src/main/java/org/telegram/ui/PrivacySettingsActivity.java"
    content = modified[path]

    # Header bind
    old_h = '''                    } else if (position == newChatsHeaderRow) {
                        headerCell.setText(getString("NewChatsFromNonContacts", R.string.NewChatsFromNonContacts));
                    }
                    break;
                case 3:'''
    new_h = '''                    } else if (position == newChatsHeaderRow) {
                        headerCell.setText(getString("NewChatsFromNonContacts", R.string.NewChatsFromNonContacts));
                    } else if (position == geminiSectionRow) {
                        headerCell.setText("Gemini xavfsizlik (Tiflogram)");
                    }
                    break;
                case 3:'''
    if old_h in content:
        content = content.replace(old_h, new_h, 1)
        print("✅ onBind header")
    else:
        print("⚠️ onBind header topilmadi")

    # TextCheck bind - after secretWebpage
    old_c = '''                    if (position == secretWebpageRow) {
                        textCheckCell.setTextAndCheck(getString("SecretWebPage", R.string.SecretWebPage), getMessagesController().secretWebpagePreview == 1, false);'''
    new_c = '''                    if (position == geminiEnableRow) {
                        textCheckCell.setTextAndCheck("Gemini skanerni yoqish", org.telegram.messenger.GeminiSafetyScanner.isEnabled() || org.telegram.messenger.GeminiSafetyScanner.prefs().getBoolean(org.telegram.messenger.GeminiSafetyScanner.KEY_ENABLED, false), true);
                    } else if (position == geminiAutoDeleteRow) {
                        textCheckCell.setTextAndCheck("Shubhalilarni avtomatik o'chirish", org.telegram.messenger.GeminiSafetyScanner.isAutoDelete(), true);
                    } else if (position == secretWebpageRow) {
                        textCheckCell.setTextAndCheck(getString("SecretWebPage", R.string.SecretWebPage), getMessagesController().secretWebpagePreview == 1, false);'''
    if old_c in content:
        content = content.replace(old_c, new_c, 1)
        print("✅ onBind checks")
    else:
        print("⚠️ onBind checks topilmadi")

    # TextSettings for API key - inject at start of case 0 after textCell.setBetterLayout
    old_s = '''                    TextSettingsCell textCell = (TextSettingsCell) holder.itemView;
                    textCell.setBetterLayout(true);
                    if (position == webSessionsRow) {'''
    new_s = '''                    TextSettingsCell textCell = (TextSettingsCell) holder.itemView;
                    textCell.setBetterLayout(true);
                    if (position == geminiApiRow) {
                        String key = org.telegram.messenger.GeminiSafetyScanner.getApiKey();
                        String shown = key.isEmpty() ? "Kiritilmagan" : (key.length() > 8 ? key.substring(0, 4) + "…" + key.substring(key.length() - 4) : "****");
                        textCell.setTextAndValue("Gemini API kalit", shown, true);
                    } else if (position == geminiScanNowRow) {
                        textCell.setText("Hozir tekshirish", true);
                    } else if (position == webSessionsRow) {'''
    if old_s in content:
        content = content.replace(old_s, new_s, 1)
        print("✅ onBind settings")
    else:
        print("⚠️ onBind settings topilmadi")

    # Detail info
    old_d = '''            } else if (position == privacyShadowRow || position == deleteAccountDetailRow || position == groupsDetailRow || position == sessionsDetailRow || position == secretDetailRow || position == botsDetailRow || position == contactsDetailRow || position == newChatsSectionRow) {
                return 1;'''
    # already patched in FIXES id 5

    # Info cell bind - find TextInfoPrivacyCell binding
    if 'geminiDetailRow' in content and 'gemini-3.5-flash-lite' not in content:
        # try inject in case 1 bind
        marker = 'TextInfoPrivacyCell privacyCell = (TextInfoPrivacyCell) holder.itemView;'
        if marker in content:
            content = content.replace(marker, marker + '''
                    if (position == geminiDetailRow) {
                        privacyCell.setText("Har 24 soatda gemini-3.5-flash-lite modeli kanal, guruh va botlarni tekshiradi. Shubhali topilsa (agar yoqilgan bo'lsa) o'chiradi. API kalit: aistudio.google.com");
                        break;
                    }''', 1)
            print("✅ onBind detail")

    # onItemClick handlers
    old_click = '''            if (position == autoDeleteMesages) {
                if (getUserConfig().getGlobalTTl() >= 0) {
                    presentFragment(new AutoDeleteMessagesActivity());
                }
            } else if (position == blockedRow) {'''
    new_click = '''            if (position == geminiApiRow) {
                if (getParentActivity() == null) return;
                final org.telegram.ui.Components.EditTextBoldCursor edit = new org.telegram.ui.Components.EditTextBoldCursor(getParentActivity());
                edit.setTextSize(android.util.TypedValue.COMPLEX_UNIT_DIP, 16);
                edit.setTextColor(Theme.getColor(Theme.key_dialogTextBlack));
                edit.setHint("AIza...");
                edit.setText(org.telegram.messenger.GeminiSafetyScanner.getApiKey());
                edit.setSingleLine(true);
                edit.setPadding(AndroidUtilities.dp(16), AndroidUtilities.dp(12), AndroidUtilities.dp(16), AndroidUtilities.dp(12));
                AlertDialog.Builder b = new AlertDialog.Builder(getParentActivity());
                b.setTitle("Gemini API kalit");
                b.setView(edit);
                b.setPositiveButton(getString(R.string.OK), (d, w) -> {
                    org.telegram.messenger.GeminiSafetyScanner.setApiKey(edit.getText() != null ? edit.getText().toString() : "");
                    if (listAdapter != null) listAdapter.notifyDataSetChanged();
                });
                b.setNegativeButton(getString(R.string.Cancel), null);
                b.show();
            } else if (position == geminiEnableRow) {
                boolean next = !org.telegram.messenger.GeminiSafetyScanner.prefs().getBoolean(org.telegram.messenger.GeminiSafetyScanner.KEY_ENABLED, false);
                org.telegram.messenger.GeminiSafetyScanner.setEnabled(next);
                if (view instanceof TextCheckCell) ((TextCheckCell) view).setChecked(next);
                if (next) org.telegram.messenger.GeminiSafetyScanner.scheduleIfNeeded();
            } else if (position == geminiAutoDeleteRow) {
                boolean next = !org.telegram.messenger.GeminiSafetyScanner.isAutoDelete();
                org.telegram.messenger.GeminiSafetyScanner.setAutoDelete(next);
                if (view instanceof TextCheckCell) ((TextCheckCell) view).setChecked(next);
            } else if (position == geminiScanNowRow) {
                if (!org.telegram.messenger.GeminiSafetyScanner.isEnabled()) {
                    org.telegram.ui.Components.BulletinFactory.of(PrivacySettingsActivity.this).createSimpleBulletin(R.raw.error, "Avval API kalit va skanerni yoqing").show();
                    return;
                }
                org.telegram.ui.Components.BulletinFactory.of(PrivacySettingsActivity.this).createSimpleBulletin(R.raw.contact_check, "Tekshiruv boshlandi…").show();
                org.telegram.messenger.Utilities.globalQueue.postRunnable(() -> org.telegram.messenger.GeminiSafetyScanner.runScan(currentAccount));
            } else if (position == autoDeleteMesages) {
                if (getUserConfig().getGlobalTTl() >= 0) {
                    presentFragment(new AutoDeleteMessagesActivity());
                }
            } else if (position == blockedRow) {'''
    if old_click in content:
        content = content.replace(old_click, new_click, 1)
        print("✅ onItemClick")
    else:
        print("⚠️ onItemClick topilmadi")

    modified[path] = content

    for pth, cnt in modified.items():
        with open(pth, "w", encoding="utf-8") as f:
            f.write(cnt)
        print(f"✅ Yozildi: {pth}")
    print("\n✅ Gemini patchlar qo'llandi (model: gemini-3.5-flash-lite)")


if __name__ == "__main__":
    main()
