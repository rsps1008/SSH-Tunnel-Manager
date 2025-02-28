# SSH Tunnel Manager GUI

This project is a GUI-based SSH Tunnel Manager built with Python and Tkinter. It allows you to manage multiple SSH tunnel configurations and control their activation, deactivation, and monitoring through an intuitive graphical interface. The application supports system tray minimization and automatic reconnection for failed tunnels.

## Features

### - Multiple Tunnel Configurations  
The interface displays 5 tunnel configurations by default, supporting up to 10. Each configuration includes:
- **Local Port**
- **Target IP**
- **Target Port**
- **Remarks field**

### - Global Settings  
Configure the remote jump server and password. These settings are saved on the first line of the configuration file `ssh通道.config` in the following format:  
```
GLOBAL,remote_jump_server,password
```
Example:  
```
GLOBAL,example_user@your.remote.host,YourSecretPassword
```

### - Dynamic Status Updates  
- Every **3 seconds**, the application automatically checks the status of each tunnel.
- **Green indicator** means the tunnel is connected.
- **Red indicator** indicates a failure, and disconnected tunnels will automatically attempt to reconnect.

### - Non-blocking Operation  
- Tunnel activation, deactivation, and status checking are performed in **background threads**, ensuring the GUI remains responsive.

### - System Tray Support  
- When minimized, the application hides in the system tray.
- Users can restore the window by clicking the tray icon.
- The tray menu allows easy access to restore or exit the application.

### - DPI Support  
- On **Windows high-DPI** screens, the application **automatically adjusts font size and interface scaling** to improve clarity.

### - Configuration Saving  
- When the application closes, all settings are automatically **saved** to `ssh通道.config` and reloaded the next time the program is run.

## Requirements

- Python 3.x  
- OpenSSH Client (ensure the `ssh` command is available)  
- `paramiko` (for SSH connections)  
- `pystray` and `Pillow` (for system tray support)  
- `sshpass` (optional: install if you need password-based authentication)

## Installation

Install required dependencies using:
```
pip install paramiko pystray pillow requests
```

## Usage

### 1. **Configuration Setup**  
On first run, if `ssh通道.config` does not exist, it will be created automatically. You may also manually edit this file using the following format:
- The first line contains global settings (remote jump server and password):  
  ```
  GLOBAL,remote_jump_server,password
  ```
  Example:
  ```
  GLOBAL,example_user@your.remote.host,YourSecretPassword
  ```
- Each subsequent line defines a tunnel configuration in the following format:  
  ```
  local_port,target_ip,target_port,remarks
  ```
  Example:
  ```
  8052,192.168.1.100,80,Tunnel 1 Remarks
  ```

### 2. **Running the Application**  
Run the application from the command line:
```
python your_script_name.py
```

### 3. **Using the GUI**  
- In the global settings section at the top, enter or confirm the **remote jump server and password** (avoid hardcoding sensitive information).  
- In the tunnel configuration section, fill in the **local port, target IP, target port, and remarks** for each tunnel.  
- Click **"Enable All Tunnels"** to start the SSH tunnels and **"Disable All Tunnels"** to stop them.  
- The status area displays the connection status of each tunnel:
  - **Green** indicates a successful connection.
  - **Red** indicates a failure (with automatic reconnection attempts).

### 4. **Minimizing to System Tray**
- If minimized, the application will hide in the **system tray**.
- Right-click the tray icon to **restore** or **exit** the application.

## Notes

### - Protect Sensitive Information  
Avoid hardcoding sensitive data (like passwords) in the source code. Use configuration files or manual input at runtime instead.

### - SSHPass Installation  
If password-based authentication is required, ensure that `sshpass` is installed. For example, on Linux:
```
sudo apt-get install sshpass
```

### - Editing Hosts File  
The application provides a button to **edit the system hosts file** with administrator permissions:
- **Windows:** Uses Notepad as administrator.
- **macOS/Linux:** Uses appropriate text editors with root privileges.

## Contributions and Licensing

- Contributions via **Issues and Pull Requests** are welcome. Please remove or mask any sensitive information before submission.  
- This project is licensed under the [CC 4.0 BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) license. Please retain this notice when referencing or modifying the project.

---

# SSH 通道管理 GUI

本專案是一個使用 **Python 與 Tkinter** 製作的 SSH 隧道管理工具，可用來管理多組 SSH 通道設定，並透過 **圖形介面** 操作各通道的啟用、停用與狀態監控。支援 **系統匣功能**，最小化時會隱藏到系統匣。

## 功能特點

### - 多組通道設定  
- 預設顯示 **5 組**，最多支援 **10 組**。
- 每組包含：
  - **本地 Port**
  - **對方 IP**
  - **對方 Port**
  - **備註**

### - 全域設定  
- 設定遠端跳板伺服器與密碼，儲存於 `ssh通道.config` 的第一行，格式：
  ```
  GLOBAL,遠端跳板伺服器,密碼
  ```

### - 動態狀態更新  
- 每 **3 秒** 自動檢查通道狀態。
- **綠色燈號** 代表連線成功。
- **紅色燈號** 代表連線失敗，並自動重試。

### - 非阻塞操作  
- 使用 **背景執行緒** 控制連線，確保 GUI **不會卡住**。

### - 系統匣支援  
- 最小化時，程式會隱藏到 **系統匣**。
- 右鍵系統匣圖示可 **還原視窗** 或 **退出應用程式**。

### - DPI 支援  
- 在 **Windows 高 DPI 螢幕** 上，會 **自動調整字體大小與縮放比例**。

### - 設定檔儲存  
- 程式關閉時，自動儲存 **所有設定**，下次啟動時自動載入。

## 安裝需求

```
pip install paramiko pystray pillow requests
```

## 使用方式

1. **設定 ssh通道.config**（格式與英文版相同）。
2. **執行程式**
   ```
   python your_script_name.py
   ```
3. **使用 GUI 操作通道與系統匣功能**。

## 貢獻與版權

- **歡迎提交 Issue 與 Pull Request**，請在提交前移除私人資訊。
- 本專案遵循 **[CC 4.0 BY-SA](https://creativecommons.org/licenses/by-sa/4.0/)** 版權協議。
