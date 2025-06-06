import subprocess
import os
from datetime import datetime

# 正則表達式
NAME_REGEX = r"(?:[陳林張李王劉黃吳周徐孫朱趙盧蘇蔡鄭謝郭洪楊邱廖賴潘蕭唐戴許呂馬何余宋羅傅馮阮鄧魏薛葉杜曾彭盧蔣賈汪]\p{Han}{1,4})(?!\p{Han})"
PHONE_REGEX = r"(?<!\d)(09\d{2}-?\d{3}-?\d{3}|0[2-8]-?\d{3,4}-?\d{4})(?!\d)"
ID_REGEX = r"(?<![\da-zA-Z])[A-Z][12]\d{8}"
ADDRESS_REGEX = r"(?<![\da-zA-Z])(?:台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市|苗栗縣|彰化縣|南投縣|雲林縣|屏東縣|宜蘭縣|花蓮縣|台東縣|澎湖縣|金門縣|連江縣)\p{Han}*(?:市|縣|區|鄉|鎮|村|路|街|巷|弄|樓)?(?:\d{1,5}號)?"

def scan_names(target_dir, save_to_txt=True):
    if not os.path.exists(target_dir):
        print(f"❗ 目錄 {target_dir} 不存在")
        return

    # 列出所有符合副檔名的檔案
    scanned_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith((".log", ".txt", ".csv")):
                full_path = os.path.join(root, file)
                scanned_files.append(full_path)

    if scanned_files:
        print("📄 以下檔案將進行掃描：")
        for f in scanned_files:
            print(f"  - {f}")
    else:
        print("⚠️ 找不到任何符合條件的檔案（.log / .txt / .csv）")
        
        
    print("------------------------------------------------------")
    # 建立共用的 rg 參數（除了 color 設定）
    base_cmd = [
        "rg", "--pcre2",
        "-n",
        "-I",
        "-e", NAME_REGEX,
        "-e", PHONE_REGEX,
        "-e", ID_REGEX,
        "-e", ADDRESS_REGEX,
        target_dir,
        "--glob", "*.log",
        "--glob", "*.txt",
        "--glob", "*.csv"
    ]
    

    try:
        # --- 顯示用（有顏色） ---
        cmd_color = base_cmd.copy()
        cmd_color.insert(3, "--color=always")
        subprocess.run(cmd_color)

        # --- 儲存用（無顏色） ---
        cmd_plain = base_cmd.copy()
        cmd_plain.insert(3, "--color=never")  # 插入到 -I 後面

        result = subprocess.run(
            cmd_plain,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"scan_result_{timestamp}.txt"
        
        output_lines = []

        if result.stdout:
            output_lines.append("🔍 找到可疑資料（姓名、電話、身分證字號或地址）：\n" + result.stdout.strip())
        else:
            output_lines.append("✅ 沒發現可疑姓名、電話、身分證字號或地址")
            
            

        if result.stderr:
            output_lines.append(f"\n⚠️ 錯誤訊息：\n{result.stderr.strip()}")

        final_output = "\n".join(output_lines)

        if save_to_txt:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(final_output)
            print(f"\n📝 結果已儲存到：{output_file}")
            
        return final_output

    except FileNotFoundError:
        print("❗ 請確認是否已安裝 ripgrep (rg 指令)")
    except Exception as e:
        print(f"⚠️ 執行錯誤：{str(e)}")

if __name__ == "__main__":
    default_dir = r"D:\nbudw\logs\test"
    user_input = input(f"請輸入要掃描的目錄（預設：{default_dir}）：\n").strip()
    target_dir = user_input if user_input else default_dir
    scan_names(target_dir)
    input("\n🔍 掃描完成，按 Enter 鍵關閉視窗...")
