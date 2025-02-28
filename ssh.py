import tkinter as tk
from tkinter import PhotoImage
from tkinter import messagebox
import subprocess
import socket
import os
import threading
import select
import errno
import sys
import tempfile
import requests
import pystray  # 系統匣支援
from pystray import MenuItem as item
from PIL import Image  # pystray 需要 PIL 處理圖像

CONFIG_FILE = "ssh通道.config"
MAX_ROWS = 10
DEFAULT_ROWS = 5

import paramiko

def get_temp_dir():
    """取得適合的暫存目錄"""
    if sys.platform.startswith("win"):
        return os.environ.get("TEMP", tempfile.gettempdir())  # Windows
    elif sys.platform.startswith("darwin"):
        return "/tmp"  # macOS
    else:
        return tempfile.gettempdir()  # Linux

def download_image(url, filename="ssh_tunnel.png"):
    """從網址下載圖片並存入暫存目錄下的 ssh_tunnel_rsps1008 資料夾"""
    temp_dir = get_temp_dir()
    folder_path = os.path.join(temp_dir, "ssh_tunnel_rsps1008")
    
    # 若資料夾不存在，則新增資料夾
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    file_path = os.path.join(folder_path, filename)
    
    # 若檔案已存在，直接回傳檔案路徑
    if os.path.exists(file_path):
        return file_path
    
    # 檔案不存在時，下載圖片
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(response.content)
        return file_path
    return None

def forward_tunnel(local_port, remote_host, remote_port, transport):
    """
    建立本地端口轉發，並回傳監聽 socket 以及 handler 線程。
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", local_port))
    except Exception as e:
        print(f"❌ 無法綁定本機端口 {local_port}: {e}")
        return None, None

    sock.listen(5)
    print(f"🚀 本機端口 {local_port} 開始監聽，轉發到 {remote_host}:{remote_port}")

    def handler():
        while True:
            try:
                client_socket, addr = sock.accept()
                channel = transport.open_channel(
                    "direct-tcpip", (remote_host, remote_port), addr
                )
                if channel is None:
                    print(f"❌ 無法開啟通道，請確認 SSH 設定是否允許轉發")
                    client_socket.close()
                    continue
                threading.Thread(target=transfer, args=(client_socket, channel), daemon=True).start()
            except OSError as e:
                if e.errno != errno.WSAENOTSOCK:  # 10038 對應的錯誤碼
                    print(f"⚠️ 其他 socket 錯誤: {e}")
            except Exception as e:
                print(f"⚠️ 轉發失敗: {e}")
                break
        sock.close()

    t = threading.Thread(target=handler, daemon=True)
    t.start()
    return sock, t

def transfer(source, destination):
    while True:
        try:
            r, w, x = select.select([source, destination], [], [])
            if source in r:
                data = source.recv(1024)
                if len(data) == 0:
                    break
                destination.send(data)
            if destination in r:
                data = destination.recv(1024)
                if len(data) == 0:
                    break
                source.send(data)
        except Exception as e:
            print(f"⚠️ 資料轉發錯誤: {e}")
            break
    source.close()
    destination.close()

class TunnelRow:
    def __init__(self, master, row, app):
        self.app = app
        self.frame = tk.Frame(master)
        self.frame.grid(row=row, column=0, padx=5, pady=2, sticky="w")

        # 輸入欄位
        self.local_entry = tk.Entry(self.frame, width=8)
        self.target_ip_entry = tk.Entry(self.frame, width=14)
        self.target_port_entry = tk.Entry(self.frame, width=8)
        self.remark_entry = tk.Entry(self.frame, width=14)

        self.local_entry.grid(row=0, column=0, padx=2)
        self.target_ip_entry.grid(row=0, column=1, padx=2)
        self.target_port_entry.grid(row=0, column=2, padx=2)
        self.remark_entry.grid(row=0, column=3, padx=2)

        # 狀態燈
        self.status_label = tk.Label(self.frame, text="●", fg="red", font=("Arial", 25), anchor="center", justify="center", width=4)
        self.status_label.grid(row=0, column=4, padx=0, sticky="nsew")
        

        # 是否啟用此通道的 Checkbutton
        self.enable_var = tk.BooleanVar(value=False)
        self.checkbutton = tk.Checkbutton(self.frame, variable=self.enable_var, command=self.on_check_change, anchor="center", justify="center", width=3)
        self.checkbutton.grid(row=0, column=5, padx=5)
        
        self.frame.grid_columnconfigure(4, weight=1)

        # SSH 相關變數
        self.ssh_client = None
        self.transport = None
        self.tunnel_socket = None  # 確保變數初始化
        self.tunnel_thread = None  # 確保變數初始化
        self.connected = False
        
        self.checkbutton = tk.Checkbutton(
            self.frame,
            variable=self.enable_var,
            command=self.on_check_change,
            anchor="center",
            justify="center",
            width=40,   # 可以調整數值
            height=50,  # 可以調整數值
            indicatoron=0  # 取消預設的勾選框
        )


    def get_values(self):
        return (
            self.local_entry.get().strip(),
            self.target_ip_entry.get().strip(),
            self.target_port_entry.get().strip(),
            self.remark_entry.get().strip()
        )

    def on_check_change(self):
        """
        Checkbutton 狀態改變時會被呼叫。
        如果勾選，就檢查欄位是否有效；若無效，立刻取消勾選。
        若有效，則以執行緒方式嘗試建立隧道；
        如果取消勾選，就以執行緒方式停止隧道。
        """
        if self.enable_var.get():
            # 使用者勾選 -> 檢查欄位
            local_port, target_ip, target_port, _ = self.get_values()
            if not (local_port and target_ip and target_port):
                # 若欄位未填寫完整，就立刻取消勾選
                print("本地 Port、對方 IP、對方 Port 有未填寫，取消勾選。")
                self.enable_var.set(False)
                return
            else:
                # 欄位都填了 -> 使用執行緒連線
                threading.Thread(target=self.start_tunnel, daemon=True).start()
        else:
            # 使用者取消勾選 -> 使用執行緒停止隧道
            threading.Thread(target=self.stop_tunnel, daemon=True).start()

    def start_tunnel(self):
        local_port, target_ip, target_port, _ = self.get_values()
        remote_server = self.app.remote_entry.get().strip()
        password = self.app.password_entry.get().strip()

        if "@" not in remote_server:
            print(f"錯誤：遠端伺服器格式錯誤 {remote_server}，請使用 user@host")
            self.set_status("red")
            return

        ssh_user, ssh_host = remote_server.split("@")
        try:
            print(f"嘗試連線到 {ssh_host}，使用帳號 {ssh_user}...")
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(ssh_host, port=22, username=ssh_user, password=password,
                                    timeout=5, banner_timeout=5, auth_timeout=5)
            self.transport = self.ssh_client.get_transport()
            self.transport.set_keepalive(30)

            # 保存 forward_tunnel 回傳的監聽 socket 與 handler 線程
            self.tunnel_socket, self.tunnel_thread = forward_tunnel(
                int(local_port), target_ip, int(target_port), self.transport
            )
            self.connected = True
            self.set_status("green")
            print(f"✅ 成功建立隧道: {local_port} -> {target_ip}:{target_port}")

        except Exception as e:
            self.connected = False
            self.set_status("red")
            print(f"❌ SSH 連線失敗: {e}")

            if self.enable_var.get():
                print(f"10 秒後再次嘗試通道：{local_port} -> {target_ip}:{target_port}")
                threading.Timer(10.0, self.start_tunnel).start()

    def stop_tunnel(self):
        if self.tunnel_socket:
            try:
                self.tunnel_socket.close()
                print("監聽 socket 已關閉")
            except Exception as e:
                print(f"關閉監聽 socket 時發生錯誤: {e}")
            self.tunnel_socket = None

        if self.transport:
            try:
                self.transport.close()
                print("SSH 連線已關閉")
            except Exception as e:
                print(f"關閉 SSH 連線時發生錯誤: {e}")
            self.transport = None

        if self.ssh_client:
            try:
                self.ssh_client.close()
                print("SSH 客戶端已關閉")
            except Exception as e:
                print(f"關閉 SSH 客戶端時發生錯誤: {e}")
            self.ssh_client = None

        self.connected = False
        self.set_status("red")
        
    def set_status(self, color):
        # 使用 after 回到主執行緒更新 GUI
        def _update():
            self.status_label.config(fg=color)
        self.app.master.after(0, _update)

class App:
    def __init__(self, master):
        self.master = master
        master.title("SSH 通道管理")

        # 全域設定：遠端伺服器與密碼
        self.config_frame = tk.Frame(master)
        self.config_frame.pack(padx=10, pady=5)
        tk.Label(self.config_frame, text="遠端伺服器", width=12).grid(row=0, column=0, padx=5, sticky="w")
        self.remote_entry = tk.Entry(self.config_frame, width=30)
        self.remote_entry.insert(0, "user@x.x.x.x")
        self.remote_entry.grid(row=0, column=1, padx=5, sticky="w")

        tk.Label(self.config_frame, text="密碼", width=12).grid(row=1, column=0, padx=5, sticky="w")
        self.password_entry = tk.Entry(self.config_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, sticky="w")

        # 通道資訊
        self.tunnel_rows = []

        # 通道設定區塊
        self.row_frame = tk.Frame(master)
        self.row_frame.pack(padx=10, pady=10)
        header = tk.Frame(self.row_frame)
        header.grid(row=0, column=0, sticky="w")
        tk.Label(header, text="本地 Port", width=8).grid(row=0, column=0, padx=2)
        tk.Label(header, text="對方 IP", width=14).grid(row=0, column=1, padx=2)
        tk.Label(header, text="對方 Port", width=8).grid(row=0, column=2, padx=2)
        tk.Label(header, text="備註", width=14).grid(row=0, column=3, padx=2)
        tk.Label(header, text="狀態", width=5).grid(row=0, column=4, padx=10)
        tk.Label(header, text="啟用", width=5).grid(row=0, column=5, padx=5)

        self.rows_container = tk.Frame(self.row_frame)
        self.rows_container.grid(row=1, column=0, sticky="w")

        # 初始化預設列
        for i in range(DEFAULT_ROWS):
            self.add_row()

        # 下方按鈕：全部啟用、全部停用、及 新增通道
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=5)

        self.enable_button = tk.Button(self.button_frame, text="全部啟用", command=self.enable_all)
        self.enable_button.grid(row=0, column=0, padx=5)

        self.disable_button = tk.Button(self.button_frame, text="全部停用", command=self.disable_all)
        self.disable_button.grid(row=0, column=1, padx=5)

        self.add_button = tk.Button(self.button_frame, text="新增通道", command=self.add_row)
        self.add_button.grid(row=0, column=2, padx=5)

        # 載入設定檔（不會載入勾選狀態）
        self.load_config()
       
        # 打開 host 檔案
        self.edit_hosts_button = tk.Button(self.button_frame, text="編輯 hosts", command=self.open_hosts_file)
        self.edit_hosts_button.grid(row=0, column=3, padx=5)
        
        # 儲存 config 檔案
        self.save_config_button = tk.Button(self.button_frame, text="儲存 config", command=self.save_config_button)
        self.save_config_button.grid(row=0, column=4, padx=5)
        
        image_url = "https://filedn.com/lv23Kcszmo74qetwMgmdPw8/shared/ssh_tunnel.png"
        self.icon_path = download_image(image_url)  # 確保 icon_path 存在
        
        if self.icon_path:
            self.icon_image = PhotoImage(file=self.icon_path)
            master.wm_iconphoto(True, self.icon_image)  # 設定 Tkinter 圖示

        # 關閉視窗事件
        # 設定「X」按鈕直接關閉程式
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 監聽最小化事件
        self.master.bind("<Unmap>", self.on_minimize)
        self.create_tray_icon()  # 啟動系統匣

    def restore_window(self, icon, item):
        """從系統匣恢復窗口"""
        self.master.deiconify()  # 顯示窗口
        self.tray_icon.visible = False  # 隱藏系統匣圖示
    
    def on_minimize(self, event):
        """當使用者點擊最小化時，隱藏 Tkinter 窗口，並顯示到系統匣"""
        if self.master.state() == "iconic":  # 確保是最小化狀態
            self.master.withdraw()  # 隱藏窗口
            self.tray_icon.visible = True  # 顯示系統匣圖示
    
    def on_closing(self):
        """退出應用程式"""
        self.tray_icon.stop()  # 停止系統匣
        self.master.destroy()  # 關閉 Tkinter 應用

    def create_tray_icon(self):
        """建立系統匣圖示"""
        if not self.icon_path:
            return

        # 轉換圖示為 PIL 格式
        icon_image = Image.open(self.icon_path)

        # 建立系統匣圖示
        self.tray_icon = pystray.Icon("SSH 管理程式", icon_image, "SSH 管理程式", menu=pystray.Menu(
            pystray.MenuItem("還原程式", self.restore_window, default=True),
            pystray.MenuItem("退出程式", self.on_closing)
        ))
        self.tray_icon.icon = icon_image
        self.tray_icon.visible = False
        self.tray_icon.on_click = self.restore_window

        # 以執行緒方式啟動系統匣
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def save_config_button(self):
        self.save_config()
        messagebox.showinfo("提示", "設定檔已儲存")
        
    def open_hosts_file(self):
        import sys, subprocess
        if sys.platform.startswith('win'):
            # Windows 系統
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            import ctypes
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "notepad.exe", hosts_path, None, 1)
            if ret <= 32:
                messagebox.showerror("錯誤", "無法以管理員身份開啟 hosts 檔案")
        elif sys.platform.startswith('darwin'):
            # macOS 系統
            hosts_path = "/etc/hosts"
            # 使用 AppleScript 以管理員權限開啟 TextEdit
            apple_script = f'do shell script "open -a TextEdit {hosts_path}" with administrator privileges'
            try:
                subprocess.run(["osascript", "-e", apple_script], check=True)
            except subprocess.CalledProcessError:
                messagebox.showerror("錯誤", "無法以管理員權限打開 hosts 檔案")
        else:
            # 假設為 Linux 系統
            hosts_path = "/etc/hosts"
            # 這邊使用 pkexec 呼叫 gedit，若系統沒有 gedit 可視需求替換編輯器
            try:
                subprocess.run(["pkexec", "gedit", hosts_path], check=True)
            except Exception as e:
                messagebox.showerror("錯誤", f"無法以管理員權限打開 hosts 檔案: {e}")

    def add_row(self):
        if len(self.tunnel_rows) >= MAX_ROWS:
            messagebox.showinfo("提示", f"最多只能新增 {MAX_ROWS} 組通道")
            return
        row = TunnelRow(self.rows_container, row=len(self.tunnel_rows), app=self)
        self.tunnel_rows.append(row)

    def enable_all(self):
        """
        全部啟用：若本地 Port、對方 IP、對方 Port 三欄都有填寫，才勾選，否則跳過。
        """
        for row in self.tunnel_rows:
            local_port, target_ip, target_port, _ = row.get_values()
            if local_port and target_ip and target_port:
                row.enable_var.set(True)
                row.on_check_change()
            else:
                row.enable_var.set(False)
                row.on_check_change()

    def disable_all(self):
        """全部停用：直接把所有通道都取消勾選。"""
        for row in self.tunnel_rows:
            row.enable_var.set(False)
            row.on_check_change()

    def load_config(self):
        """
        載入檔案時，只讀取本地 Port、對方 IP、對方 Port、備註四欄。
        不載入「啟用狀態」，預設一律為未勾選。
        """
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
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
                    lines = lines[1:]  # 移除全域設定行

                # 若檔案中的通道數量 > 目前 rows，就動態增加 rows
                while len(lines) > len(self.tunnel_rows) and len(self.tunnel_rows) < MAX_ROWS:
                    self.add_row()

                # 逐行讀取每條通道設定 (只載入四個欄位)
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

                    # 啟用狀態不讀，預設不勾選

            except Exception as e:
                print("載入設定失敗:", e)

    def save_config(self):
        """
        存檔時，只記錄本地 Port、對方 IP、對方 Port、備註。
        不紀錄「啟用狀態」，因為需求是每次啟動都預設關閉。
        """
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
        try:
            with open(config_path , "w", encoding="utf-8") as f:
                # 寫入全域設定行
                remote = self.remote_entry.get().strip()
                password = self.password_entry.get().strip()
                f.write(f"GLOBAL,{remote},{password}\n")

                # 寫入各通道設定: local, ip, port, remark
                for row in self.tunnel_rows:
                    local, ip, port, remark = row.get_values()
                    f.write(f"{local},{ip},{port},{remark}\n")
        except Exception as e:
            print("儲存設定失敗:", e)

    def on_closing(self):
        # 離開前，先停止所有已啟用的 SSH 連線
        for row in self.tunnel_rows:
            row.stop_tunnel()
        self.save_config()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # DPI 相關設定，解決高 DPI 螢幕下的字體與介面模糊問題 (Windows)
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
