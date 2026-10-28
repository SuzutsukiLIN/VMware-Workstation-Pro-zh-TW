# VMware Workstation Pro 26H1 繁體中文化研究紀錄

**繁體中文（台灣） · v1.2 · VMware Workstation Pro 26.0.1（build 25688693）**

> [!NOTE]
> 本專案為非官方的中文化學習、相容性研究及實機測試紀錄，與 VMware／Broadcom 無關；不是官方語言套件。

## 下載 v1.2 一鍵安裝包

**[下載 VMware 26.0.1 繁體中文 v1.2 一鍵安裝 ZIP](downloads/VMware_Workstation_26.0.1_zhTW_v1.2_OneClick.zip)**

SHA-256：`3800b819a08c5b5399d555720e0ab668dd9b26a8ac92f3aa848aaaa9d0d06ded`

此 ZIP **直接包含已測試的 v1.2 語系檔、安裝器與還原工具**，一般使用者不需要 VM17 繁中 ZIP、ES 語系 ZIP，也不需要 Python。安裝器與三份語系檔內容和實機驗收版一致；本次重新封裝只調整說明文件，發布 ZIP 尚未另做乾淨 Windows 首次安裝驗收。

### 安裝方式

1. 在 Windows x64 安裝 **VMware Workstation Pro 26.0.1（build 25688693）**；請先關閉 VMware 主程式。
2. 下載 ZIP 並**完整解壓縮**，雙擊 `Install.cmd`，依指示允許系統管理員權限。
3. 安裝器會檢查版本與檔案雜湊、備份原有 ES 語系資源、安裝繁體中文，並在桌面建立 **「VMware Workstation Pro - 繁體中文」** 捷徑。
4. 之後直接雙擊桌面捷徑啟動，不必修改 `preferences.ini`。

**還原：** 完全關閉 VMware 後執行 ZIP 中的 `Uninstall.cmd`。解除安裝／還原流程已實作，但尚未完成不同電腦的完整驗收。

## 研究成果

新版 VMware 若沿用舊版 `messages\\zh_TW`，部分精靈介面仍會退回英文。經過 `.vmsg` 字串比對、Win32 對話框資源檢查、原生 ES 語系對照，以及資源載入測試，確認可以利用 **26.0.1 原生 ES 資源識別碼與檔名**，將介面內容改為繁體中文，並以 `vmware.exe --locale=es` 啟動。

- **v1.0：** ES 相容模式成功，精靈介面顯示中文。
- **v1.1：** 改善 TPM 選項、密碼欄位標籤及台灣用語。
- **v1.2：** 精簡部分介面說明，改善排版；整合一鍵安裝與桌面捷徑。
- **已實機測試：** 精靈主要頁面、繁體中文介面、安裝及桌面捷徑。
- **尚未全面驗證：** 所有設定介面、不同 DPI、首次安裝於全新系統與完整解除安裝。

完整過程請見 [研究紀錄](docs/RESEARCH_LOG.md)。

## 安全與相容性

- 僅支援 **26.0.1 build 25688693**。其他版本的資源識別碼可能不同；不要強制覆蓋。
- 修改過的 DLL 不再具有有效的原廠數位簽章。請自行評估 Windows 安全政策。
- 本專案不修改 VMware 主程式或虛擬機影像；安裝前仍建議備份。
- 動態字串（例如 `Workstation 25H2 or later`）及尚未驗收畫面可能仍有英文。

## 專案檔案

- [v1.2 完整安裝 ZIP](downloads/VMware_Workstation_26.0.1_zhTW_v1.2_OneClick.zip)：**一般使用者請下載這份**。
- `Install.cmd`、`Uninstall.cmd`、`scripts/`：安裝器原始碼。
- `builder/` 與 [開發者建置說明](docs/DEVELOPER_BUILD.md)：研究重現與維護用，**一般使用者不需要執行**。
- `docs/`：版本演進、測試記錄及技術說明。

## 授權與免責聲明

**本 ZIP 含有修改過的 VMware 專有語系 DLL 與 `.vmsg`。** 這些檔案及原廠文字、商標不因公開在本倉庫就取得 MIT 授權；原創安裝器程式碼的 MIT 授權僅適用原創部分。此研究性質的發布不代表已獲 Broadcom 再散布許可；使用、改作與再散布仍應遵守權利人授權及適用法律。詳見 [NOTICE.md](NOTICE.md)。

本專案不提供 VMware 安裝程式、產品金鑰或繞過產品授權的功能。
