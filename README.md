# SSH Tunnel Manager GUI

This project is a GUI-based SSH Tunnel Manager built with Python and Tkinter. It allows you to manage multiple SSH tunnel configurations and control their activation, deactivation, and monitoring through an intuitive graphical interface.

## Features

- Multiple Tunnel Configurations  
  The interface displays 5 tunnel configurations by default, supporting up to 10. Each configuration includes a local Port, target IP, target Port, and a remarks field.

- Global Settings  
  Configure the remote jump server and password. These settings are saved on the first line of the configuration file "ssh通道.config" in the following format:
  GLOBAL,remote_jump_server,password

- Dynamic Status Updates  
Every 3 seconds, the application automatically checks the status of each tunnel. A green indicator means the tunnel is connected, while red indicates a failure. Disconnected tunnels will automatically attempt to reconnect.

- Non-blocking Operation  
Tunnel activation, deactivation, and status checking are performed in background threads to ensure that the GUI remains responsive.

- DPI Support  
On Windows high-DPI screens, the application automatically adjusts font size and interface scaling to improve clarity.

- Configuration Saving  
When the application closes, all settings are automatically saved to "ssh通道.config" and reloaded the next time the program is run.

## Requirements

- Python 3.x  
- OpenSSH Client (ensure the `ssh` command is available)  
- sshpass (optional: install if you need password-based authentication)

## Usage

1. **Configuration Setup**  
 On first run, if "ssh通道.config" does not exist, it will be created automatically. You may also manually edit this file using the following format:
 - The first line contains global settings (remote jump server and password):  
   ```
   GLOBAL,remote_jump_server,password
   ```
   For example:  
   ```
   GLOBAL,example_user@your.remote.host,YourSecretPassword
   ```
   
 - Each subsequent line defines a tunnel configuration in the following format:  
   ```
   local_port,target_ip,target_port,remarks
   ```
   For example:  
   ```
   8052,192.168.1.100,80,Tunnel 1 Remarks
   ```

2. **Running the Application**  
 Run the application from the command line with:  
 python your_script_name.py

3. **Using the GUI**  
- In the global settings section at the top, enter or confirm the remote jump server and password (avoid hardcoding sensitive information).  
- In the tunnel configuration section, fill in the local port, target IP, target port, and remarks for each tunnel.  
- Click "Enable All Tunnels" to start the SSH tunnels and "Disable All Tunnels" to stop them.  
- The status area displays the connection status of each tunnel: green indicates a successful connection, red indicates a failure (with automatic reconnection attempts).

## Notes

- Protect Sensitive Information  
Avoid hardcoding sensitive data (like passwords) in the source code. Use configuration files or manual input at runtime instead.

- sshpass Installation  
If password-based authentication is required, ensure that sshpass is installed (for example, on Linux you can use `apt-get install sshpass`).

## Contributions and Licensing

- Contributions via Issues and Pull Requests are welcome. Please remove or mask any sensitive information before submission.  
- This project is licensed under the [CC 4.0 BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) license. Please retain this notice when referencing or modifying the project.








# SSH 通道管理 GUI

本專案是一個使用 Python 與 Tkinter 製作的 SSH 隧道管理工具，可用來管理多組 SSH 通道設定，並透過圖形介面操作各通道的啟用、停用與狀態監控。

## 功能特點

- 多組通道設定  
  預設顯示 5 組通道，最多支援 10 組。每組包含本地 Port、對方 IP、對方 Port 與備註欄位。

- 全域設定  
  可設定遠端跳板伺服器與密碼，這兩項設定將儲存於配置檔 "ssh通道.config" 的第一行（格式：GLOBAL,遠端跳板伺服器,密碼）。

- 動態狀態更新  
  每 3 秒自動檢查通道狀態，顯示連線成功（綠燈）或失敗（紅燈），並自動重連斷線通道。

- 非阻塞操作  
  啟用、停用及狀態檢查皆在背景線程中執行，確保 GUI 流暢不受影響。

- DPI 支援  
  在 Windows 高 DPI 螢幕下可自動調整字體與介面大小，改善顯示模糊問題。

- 配置儲存  
  程式關閉時自動儲存所有設定至 "ssh通道.config"，下次啟動時自動讀取。

## 安裝需求

- Python 3.x  
- OpenSSH 客戶端（需能執行 ssh 命令）  
- sshpass（選用：若需使用密碼傳遞功能，請安裝 sshpass）

## 使用方法

1. 配置設定  
   初次執行程式時，若 "ssh通道.config" 不存在，程式將自動建立。你也可事先手動編輯此檔案，格式如下：
   - 第一行為全域設定（遠端跳板伺服器與密碼）：  
     GLOBAL,遠端跳板伺服器,密碼  
     例如：GLOBAL,example_user@your.remote.host,YourSecretPassword
     
   - 後續各行為通道設定（本地 Port, 對方 IP, 對方 Port, 備註）：  
     8052,192.168.1.100,80,通道1備註

2. 執行程式  
   在命令提示字元中執行：  
   python your_script_name.py

3. 使用 GUI  
   - 在上方全域設定區域，輸入或確認遠端跳板伺服器與密碼（請勿硬編碼私人資訊）。  
   - 在通道設定區填寫各組的本地 Port、對方 IP、對方 Port 與備註。  
   - 點擊「啟用所有通道」以啟動 SSH 隧道，點擊「停用所有通道」以關閉。  
   - 狀態區將顯示各通道連線狀態，綠色表示連線成功，紅色則表示失敗（並會自動嘗試重連）。

## 注意事項

- 私人資訊遮蔽  
  請勿將私人資訊（例如密碼）硬編碼在原始碼中，建議利用配置檔或在執行時手動輸入。

- sshpass 安裝  
  若需要使用密碼傳遞功能，請先安裝 sshpass（例如：在 Linux 上可使用 apt-get install sshpass）。

## 貢獻與版權

- 歡迎提交 Issue 與 Pull Request，請在提交前移除或遮蔽可能涉及的私人資訊。  
- 本專案遵循 [CC 4.0 BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) 版權協議，請在引用或修改時保留本聲明。
