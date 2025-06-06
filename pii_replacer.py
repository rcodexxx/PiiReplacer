# pii_replacer.py

import os
import sys
import subprocess
import regex as re

# --- 設定區 ---
# 您可以新增、修改或刪除這些正則表達式
REGEX_PATTERNS = {
    "NAME": r"(?:[陳林張李王劉黃吳周徐孫朱趙盧蘇蔡鄭謝郭洪楊邱廖賴潘蕭唐戴許呂馬何余宋羅傅馮阮鄧魏薛葉杜曾彭盧蔣賈汪]\p{Han}{1,4})(?!\p{Han})",
    "PHONE": r"(?<!\d)(09\d{2}-?\d{3}-?\d{3}|0[2-8]-?\d{3,4}-?\d{4})(?!\d)",
    "ID": r"(?<![\da-zA-Z])[A-Z][12]\d{8}",
    "ADDRESS": r"(?<![\da-zA-Z])(?:台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市|苗栗縣|彰化縣|南投縣|雲林縣|屏東縣|宜蘭縣|花蓮縣|台東縣|澎湖縣|金門縣|連江縣)\p{Han}*(?:市|縣|區|鄉|鎮|村|路|街|巷|弄|樓)?(?:\d{1,5}號)?"
}


# --- 核心功能 ---

def get_rg_path():
    """
    取得 rg 執行檔的路徑。
    如果是被 PyInstaller 封裝的 exe，則從暫存目錄中尋找。
    否則，從與腳本相同的目錄中尋找。
    """
    if getattr(sys, 'frozen', False):
        # 程式被凍結成 exe
        base_path = sys._MEIPASS
    else:
        # 正常執行 .py 腳本
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 判斷作業系統，決定執行檔名稱
    if sys.platform.startswith('win'):
        rg_executable = 'rg.exe'
    else:
        rg_executable = 'rg'

    path = os.path.join(base_path, rg_executable)
    if not os.path.exists(path):
        raise FileNotFoundError(f"無法在 '{base_path}' 中找到 '{rg_executable}'")
    return path


def process_folder(target_dir):
    """
    處理指定資料夾中的所有 .log, .txt, .csv 檔案。
    """
    print(f"[*] 目標資料夾: {target_dir}")
    try:
        RG_PATH = get_rg_path()
        print(f"[*] 使用 Ripgrep 路徑: {RG_PATH}")
    except FileNotFoundError as e:
        print(f"[!] 錯誤: {e}")
        return

    # 1. 組合所有正則表達式
    all_regex_str = "|".join(f"({p})" for p in REGEX_PATTERNS.values())
    combined_regex = re.compile(all_regex_str)

    # 2. 使用 rg 高速尋找包含個資的檔案清單
    print("[*] 正在使用 Ripgrep 搜尋檔案...")
    cmd = [
        RG_PATH, "--pcre2", "-l", "-I",
        "--glob", "*.log", "--glob", "*.txt", "--glob", "*.csv",
        "-e", all_regex_str,
        target_dir
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False
        )
        if result.returncode != 0 and result.returncode != 1:
            raise RuntimeError(f"Ripgrep 執行失敗:\n{result.stderr}")

        files_to_modify = result.stdout.strip().splitlines()
    except (RuntimeError, FileNotFoundError) as e:
        print(f"[!] 錯誤: {e}")
        return

    if not files_to_modify:
        print("[+] 掃描完成，找不到任何包含目標內容的檔案。")
        return

    print(f"[*] 發現 {len(files_to_modify)} 個檔案需要處理。")

    # 3. 逐一處理檔案
    modified_count = 0
    for filepath in files_to_modify:
        try:
            original_mtime = os.path.getmtime(filepath)

            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            modified_content, num_subs = re.subn(
                combined_regex,
                lambda m: '*' * len(m.group(0)),
                content
            )

            if num_subs > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified_content)

                os.utime(filepath, (original_mtime, original_mtime))

                print(f"  - 已修改: {os.path.basename(filepath)} ({num_subs} 處)，修改時間已還原。")
                modified_count += 1

        except Exception as e:
            print(f"  - [!] 處理失敗: {os.path.basename(filepath)}, 錯誤: {e}")

    print(f"\n[+] 全部完成！共修改了 {modified_count} 個檔案。")


if __name__ == '__main__':
    print("--- 個資取代工具 ---")

    # 讓使用者可以用拖曳資料夾的方式使用
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = input("請輸入要處理的資料夾路徑，或將資料夾拖曳至此視窗後按 Enter: ").strip().strip('"')

    if not os.path.isdir(target_dir):
        print(f"[!] 錯誤: '{target_dir}' 不是一個有效的資料夾。")
    else:
        process_folder(target_dir)

    input("\n按 Enter 鍵結束...")