import tkinter as tk
from tkinter import messagebox
import subprocess
import socket
import os
import threading

CONFIG_FILE = "ssh通道.config"
MAX_ROWS = 10
DEFAULT_ROWS = 5

class TunnelRow:
    def __init__(self, master, row, app):
        self.app = app  # 取得 App 參考，方便存取全域設定
        self.frame = tk.Frame(master)
        self.frame.grid(row=row, column=0, padx=5, pady=2, sticky="w")
        
        # 輸入欄位：本地端 Port、對方 IP、對方 Port、備註
        self.local_entry = tk.Entry(self.frame, width=6)
        self.target_ip_entry = tk.Entry(self.frame, width=14)
        self.target_port_entry = tk.Entry(self.frame, width=6)
        self.remark_entry = tk.Entry(self.frame, width=14)
        self.local_entry.grid(row=0, column=0, padx=2)
        self.target_ip_entry.grid(row=0, column=1, padx=2)
        self.target_port_entry.grid(row=0, column=2, padx=2)
        self.remark_entry.grid(row=0, column=3, padx=2)

        # 狀態燈號，以「●」符號表示，預設紅色
        self.status_label = tk.Label(self.frame, text="●", anchor="center", fg="red", font=("Arial", 24), width=4)
        self.status_label.grid(row=0, column=4)
        self.frame.grid_columnconfigure(4, weight=1)


        
        # 用來存放該通道建立的 ssh 子程序
        self.process = None
        # 標記該通道是否已啟用
        self.enabled = False

    def get_values(self):
        return (self.local_entry.get().strip(),
                self.target_ip_entry.get().strip(),
                self.target_port_entry.get().strip(),
                self.remark_entry.get().strip())

    def start_tunnel(self):
        # 從 App 取得全域遠端設定
        remote_server = self.app.remote_entry.get().strip()
        password = self.app.password_entry.get().strip()
        local_port, target_ip, target_port, _ = self.get_values()
        # 檢查必要欄位是否填寫
        if not (local_port and target_ip and target_port):
            return
        # 若已有有效進程，則不重複啟動
        if self.process and self.process.poll() is None:
            self.enabled = True
            return
        # 如果有填寫密碼則使用 sshpass，否則直接使用 ssh
        if password:
            cmd = [
                "sshpass", "-p", password,
                "ssh",
                "-o", "ServerAliveInterval=60",
                "-N",
                "-L", f"{local_port}:{target_ip}:{target_port}",
                remote_server
            ]
        else:
            cmd = [
                "ssh",
                "-o", "ServerAliveInterval=60",
                "-N",
                "-L", f"{local_port}:{target_ip}:{target_port}",
                remote_server
            ]
        try:
            self.process = subprocess.Popen(cmd)
            self.enabled = True
        except Exception as e:
            print(f"啟動隧道失敗：{e}")

    def stop_tunnel(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                print(f"停止隧道時發生錯誤：{e}")
            self.process = None
        self.enabled = False

    def update_status(self):
        # 將狀態檢查放到背景線程中執行，避免 GUI 被阻塞
        def check():
            local_port, _, _, _ = self.get_values()
            try:
                port = int(local_port)
            except:
                try:
                    self.status_label.after(0, lambda: self.status_label.config(fg="red"))
                except RuntimeError:
                    pass
                return
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            try:
                s.connect(("127.0.0.1", port))
                color = "green"
            except:
                color = "red"
                # 若通道已啟用但連線斷線，則嘗試重連
                if self.enabled:
                    print(f"通道 {local_port} 連線斷線，嘗試重連...")
                    self.stop_tunnel()
                    self.start_tunnel()
            finally:
                s.close()
            try:
                self.status_label.after(0, lambda: self.status_label.config(fg=color))
            except RuntimeError:
                pass
        threading.Thread(target=check).start()

class App:
    def __init__(self, master):
        self.master = master
        master.title("SSH 通道管理")

        # 新增全域設定區塊：遠端跳板伺服器與密碼 (密碼在下一行)
        self.config_frame = tk.Frame(master)
        self.config_frame.pack(padx=10, pady=5)
        tk.Label(self.config_frame, text="遠端跳板伺服器", width=12).grid(row=0, column=0, padx=5, sticky="w")
        self.remote_entry = tk.Entry(self.config_frame, width=30)
        self.remote_entry.insert(0, "civet@10.134.152.20")
        self.remote_entry.grid(row=0, column=1, padx=5, sticky="w")
        tk.Label(self.config_frame, text="密碼", width=12).grid(row=1, column=0, padx=5, sticky="w")
        self.password_entry = tk.Entry(self.config_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, sticky="w")

        self.tunnel_rows = []

        # 上方通道設定區塊
        self.row_frame = tk.Frame(master)
        self.row_frame.pack(padx=10, pady=10)
        header = tk.Frame(self.row_frame)
        header.grid(row=0, column=0, sticky="w")
        tk.Label(header, text="本地 Port", width=6).grid(row=0, column=0, padx=2)
        tk.Label(header, text="對方 IP", width=14).grid(row=0, column=1, padx=2)
        tk.Label(header, text="對方 Port", width=6).grid(row=0, column=2, padx=2)
        tk.Label(header, text="備註", width=14).grid(row=0, column=3, padx=2)
        tk.Label(header, text="狀態", width=5).grid(row=0, column=4, padx=8)

        self.rows_container = tk.Frame(self.row_frame)
        self.rows_container.grid(row=1, column=0, sticky="w")
        for i in range(DEFAULT_ROWS):
            self.add_row()

        # 下方按鈕區塊：啟用、停用、與新增通道按鈕
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=5)
        self.enable_button = tk.Button(self.button_frame, text="啟用所有通道", command=self.start_all)
        self.enable_button.grid(row=0, column=0, padx=5)
        self.disable_button = tk.Button(self.button_frame, text="停用所有通道", command=self.stop_all)
        self.disable_button.grid(row=0, column=1, padx=5)
        self.add_button = tk.Button(self.button_frame, text="新增通道", command=self.add_row)
        self.add_button.grid(row=0, column=2, padx=5)

        self.update_status_loop()
        self.load_config()
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_row(self):
        if len(self.tunnel_rows) >= MAX_ROWS:
            messagebox.showinfo("提示", f"最多只能新增 {MAX_ROWS} 組通道")
            return
        row = TunnelRow(self.rows_container, row=len(self.tunnel_rows), app=self)
        self.tunnel_rows.append(row)

    def start_all(self):
        # 分別在不同線程中啟動各通道
        for row in self.tunnel_rows:
            threading.Thread(target=row.start_tunnel).start()
        # 稍後再更新狀態（避免線程尚未完成）
        self.master.after(100, self.update_all_status)

    def stop_all(self):
        # 分別在不同線程中停用各通道
        for row in self.tunnel_rows:
            threading.Thread(target=row.stop_tunnel).start()
        self.master.after(100, self.update_all_status)

    def update_all_status(self):
        for row in self.tunnel_rows:
            row.update_status()

    def update_status_loop(self):
        for row in self.tunnel_rows:
            row.update_status()
        self.master.after(3000, self.update_status_loop)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # 若第一行為全域設定 (以 "GLOBAL," 為開頭)
                if len(lines) > 0 and lines[0].startswith("GLOBAL,"):
                    global_line = lines[0].strip()
                    parts = global_line.split(",")
                    if len(parts) >= 3:
                        self.remote_entry.delete(0, tk.END)
                        self.remote_entry.insert(0, parts[1])
                        self.password_entry.delete(0, tk.END)
                        self.password_entry.insert(0, parts[2])
                    # 移除全域設定行，剩下為通道設定
                    lines = lines[1:]
                while len(lines) > len(self.tunnel_rows) and len(self.tunnel_rows) < MAX_ROWS:
                    self.add_row()
                for i, line in enumerate(lines):
                    parts = line.strip().split(",")
                    if len(parts) >= 3 and i < len(self.tunnel_rows):
                        self.tunnel_rows[i].local_entry.delete(0, tk.END)
                        self.tunnel_rows[i].local_entry.insert(0, parts[0])
                        self.tunnel_rows[i].target_ip_entry.delete(0, tk.END)
                        self.tunnel_rows[i].target_ip_entry.insert(0, parts[1])
                        self.tunnel_rows[i].target_port_entry.delete(0, tk.END)
                        self.tunnel_rows[i].target_port_entry.insert(0, parts[2])
                        remark = parts[3] if len(parts) >= 4 else ""
                        self.tunnel_rows[i].remark_entry.delete(0, tk.END)
                        self.tunnel_rows[i].remark_entry.insert(0, remark)
            except Exception as e:
                print("載入設定失敗:", e)

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                # 寫入全域設定行
                remote = self.remote_entry.get().strip()
                password = self.password_entry.get().strip()
                f.write(f"GLOBAL,{remote},{password}\n")
                # 寫入各通道設定
                for row in self.tunnel_rows:
                    local, ip, port, remark = row.get_values()
                    if local or ip or port or remark:
                        f.write(f"{local},{ip},{port},{remark}\n")
        except Exception as e:
            print("儲存設定失敗:", e)

    def on_closing(self):
        self.stop_all()
        self.save_config()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # DPI 相關設定，解決高 DPI 螢幕下的字體與介面模糊問題
    try:
        from ctypes import windll
        from tkinter import font as tkfont
        import math
        windll.shcore.SetProcessDpiAwareness(1)
        scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100
        default_font = tkfont.nametofont("TkDefaultFont")
        font_size = math.ceil(10 * scale_factor)
        default_font.configure(family='Microsoft YaHei', size=font_size)
        root.option_add('*Font', default_font)

    except Exception as e:
        print("DPI 設定失敗:", e)
    app = App(root)
    root.mainloop()
