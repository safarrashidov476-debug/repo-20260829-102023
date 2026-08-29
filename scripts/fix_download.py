#!/usr/bin/env python3
"""
Tiflogram: yuklash tugashi tovushi + Tiflogram papkasiga saqlash.
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    # --- Papka nomlari: Telegram -> Tiflogram ---
    {
        "id": 1,
        "label": "ImageLoader: asosiy Telegram papkasi -> Tiflogram",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": 'new File(publicMediaDir, "Telegram")',
        "new": 'new File(publicMediaDir, "Tiflogram")',
        "replace_all": True,
    },
    {
        "id": 2,
        "label": "ImageLoader: telegramPath = .../Telegram -> Tiflogram",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": 'new File(newPath, "Telegram")',
        "new": 'new File(newPath, "Tiflogram")',
        "replace_all": True,
    },
    {
        "id": 3,
        "label": "ImageLoader: path/Telegram -> Tiflogram",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": 'new File(path, "Telegram")',
        "new": 'new File(path, "Tiflogram")',
        "replace_all": True,
    },
    {
        "id": 4,
        "label": "ImageLoader: Telegram Images -> Tiflogram Images",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": '"Telegram Images"',
        "new": '"Tiflogram Images"',
        "replace_all": True,
    },
    {
        "id": 5,
        "label": "ImageLoader: Telegram Video -> Tiflogram Video",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": '"Telegram Video"',
        "new": '"Tiflogram Video"',
        "replace_all": True,
    },
    {
        "id": 6,
        "label": "ImageLoader: Telegram Audio -> Tiflogram Audio",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": '"Telegram Audio"',
        "new": '"Tiflogram Audio"',
        "replace_all": True,
    },
    {
        "id": 7,
        "label": "ImageLoader: Telegram Documents -> Tiflogram Documents",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": '"Telegram Documents"',
        "new": '"Tiflogram Documents"',
        "replace_all": True,
    },
    {
        "id": 8,
        "label": "ImageLoader: Telegram Files -> Tiflogram Files",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": '"Telegram Files"',
        "new": '"Tiflogram Files"',
        "replace_all": True,
    },
    {
        "id": 9,
        "label": "ImageLoader: Telegram Stories -> Tiflogram Stories",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/ImageLoader.java",
        "old": '"Telegram Stories"',
        "new": '"Tiflogram Stories"',
        "replace_all": True,
    },
    # --- Yuklash tugashi: tovush + TalkBack ---
    {
        "id": 10,
        "label": "DownloadController: fileLoaded -> tovush va ogohlantirish",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java",
        "old": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];''',
        "new": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            // Tiflogram: yuklash tugadi - faqat tovush (TalkBack aytmaydi)
            try {
                android.media.MediaPlayer mp = android.media.MediaPlayer.create(
                        ApplicationLoader.applicationContext,
                        org.telegram.messenger.R.raw.sound_download);
                if (mp != null) {
                    mp.setOnCompletionListener(android.media.MediaPlayer::release);
                    mp.start();
                }
            } catch (Throwable ignore) {
            }
            listenerInProgress = true;
            String fileName = (String) args[0];''',
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

    print(f"=== Rejim: {MODE} (yuklash papkasi + tovush) ===\n")
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
        print("⛔ Hech narsa o'zgartirilmadi")
        sys.exit(1)

    modified = dict(file_cache)
    for fix in FIXES:
        path = fix["path"]
        if fix.get("replace_all"):
            modified[path] = modified[path].replace(fix["old"], fix["new"])
        else:
            modified[path] = modified[path].replace(fix["old"], fix["new"], 1)

    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")
    print("\n✅ Yuklash papkasi va tovush patchlari qo'llandi.")


if __name__ == "__main__":
    main()
