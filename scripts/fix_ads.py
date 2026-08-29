#!/usr/bin/env python3
"""
Telegram Android uchun sponsor (reklama) xabarlarini o'chirish.
Kanal va botlardagi sponsored messages + video reklamalarni bloklaydi.
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": 1,
        "label": "MessagesController.isSponsoredDisabled() -> har doim true",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java",
        "old": '''    public boolean isSponsoredDisabled() {
        TLRPC.UserFull userFull = getUserFull(getUserConfig().getClientUserId());
        if (userFull == null) return false;
        return !userFull.sponsored_enabled;
    }''',
        "new": '''    public boolean isSponsoredDisabled() {
        // Tiflogram: reklamalarni o'chirish
        return true;
    }''',
    },
    {
        "id": 2,
        "label": "MessagesController.getSponsoredMessages() -> null",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java",
        "old": '''    public SponsoredMessagesInfo getSponsoredMessages(long dialogId) {
        SponsoredMessagesInfo info = sponsoredMessages.get(dialogId);''',
        "new": '''    public SponsoredMessagesInfo getSponsoredMessages(long dialogId) {
        // Tiflogram: reklamalarni o'chirish - hech qachon so'ramaymiz
        // (o'zgaruvchi orqali: if(true) unreachable xatosini beradi)
        boolean tiflogramDisableAds = true;
        if (tiflogramDisableAds) {
            return null;
        }
        SponsoredMessagesInfo info = sponsoredMessages.get(dialogId);''',
    },
    {
        "id": 3,
        "label": "ChatActivity.addSponsoredMessages() -> darhol return",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java",
        "old": '''    private void addSponsoredMessages(boolean animated) {
        if (sponsoredMessagesAdded || chatMode != 0 || !ChatObject.isChannel(currentChat) && !UserObject.isBot(currentUser) || !forwardEndReached[0] || getUserConfig().isPremium() && getMessagesController().isSponsoredDisabled() || isReport()) {
            return;
        }''',
        "new": '''    private void addSponsoredMessages(boolean animated) {
        // Tiflogram: reklamalarni o'chirish
        // (o'zgaruvchi orqali: if(true)/return unreachable xatosini bermaydi)
        boolean tiflogramDisableAds = true;
        if (tiflogramDisableAds || sponsoredMessagesAdded || chatMode != 0 || !ChatObject.isChannel(currentChat) && !UserObject.isBot(currentUser) || !forwardEndReached[0] || getUserConfig().isPremium() && getMessagesController().isSponsoredDisabled() || isReport()) {
            return;
        }''',
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
        print(f"Noma'lum rejim: {MODE}. 'check' yoki 'apply' bo'lishi kerak.")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (reklama o'chirish) ===\n")

    results = []
    file_cache = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]

        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi: {path}")
            results.append((fix, False, "fayl topilmadi"))
            continue

        if fix["old"] not in content:
            print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
            results.append((fix, False, "eski matn topilmadi"))
            continue

        print(f"✅ [{fix['id']}] {fix['label']} — topildi")
        results.append((fix, True, None))

    failed = [r for r in results if not r[1]]

    print("\n=== Xulosa ===")
    print(f"Jami: {len(results)}, muvaffaqiyatli: {len(results) - len(failed)}, xato: {len(failed)}")

    if failed:
        print("\nXato bo'lgan tuzatishlar:")
        for fix, ok, reason in failed:
            print(f"  - [{fix['id']}] {fix['label']}: {reason}")

    if MODE == "check":
        sys.exit(1 if failed else 0)

    if failed:
        print("\n⛔ Ba'zi tuzatishlar topilmadi. Hech narsa o'zgartirilmadi (all-or-nothing).")
        sys.exit(1)

    print("\n=== Qo'llanmoqda ===")
    modified_content = dict(file_cache)

    for fix in FIXES:
        path = fix["path"]
        modified_content[path] = modified_content[path].replace(fix["old"], fix["new"], 1)

    for path, content in modified_content.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")

    print("\n✅ Barcha reklama tuzatishlari muvaffaqiyatli qo'llandi.")


if __name__ == "__main__":
    main()
