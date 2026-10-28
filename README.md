# VMware Workstation Pro 繁體中文（zh-TW）ES 相容模式

[![Status](https://img.shields.io/badge/VMware-26.0.1%20%7C%2026H1-blue)](#相容版本)

> **非官方社群專案**，與 VMware / Broadcom 無隸屬關係。開源的是**安裝器與本機語系建置工具**；原廠 DLL、完整 `.vmsg` 與任何含有 VMware 專有資源的檔案**不包含在公開原始碼及 GitHub Release**。使用者必須使用自己合法取得的來源語系檔在本機建置。

本工具將 VMware Workstation Pro 26H1 的原生西班牙文 `es` 語系資源轉為台灣繁體中文內容；透過 `vmware.exe --locale=es` 啟動。**不修改 `vmware.exe`、其他核心執行檔或個人 `preferences.ini`。**

## 相容版本

- Windows x64 上的 **VMware Workstation Pro 26.0.1 build-25688693**。
- 使用已安裝程式內的 `messages\es` 資源。其他版本**拒絕安裝**，不會強制覆蓋。
- VMware 26H1 的「新增虛擬機精靈」已由使用者進行實機驗證；繁體中文一鍵安裝與桌面捷徑亦回報測試 OK。**解除安裝、不同 DPI 與所有功能的完整中文化尚未驗收**。

## 使用方式

### 一鍵安裝（已備妥本機語系檔後）

1. 確認 VMware Workstation 已安裝，**完全關閉 VMware 主程式**。
2. 確認 `payload\es` 已有從**自己的合法來源**建置的 `vmappsdk-es.dll`、`vmui-es.dll`、`vmware.vmsg`。
3. 雙擊 **`Install.cmd`** → 同意 Windows 系統管理員權限（UAC）。
4. 安裝器自動偵測 VMware、檢查版本和 SHA-256、備份原始檔、寫入語系檔，最後在**公用桌面**建立 **`VMware Workstation Pro - 繁體中文`** 捷徑。
5. 以桌面捷徑啟動 VMware，**不必手動修改語系設定**。

桌面捷徑直接連到 `vmware.exe`，啟動參數為 `--locale=es`，不會跳出 CMD 視窗。

> 公開原始碼不附 VMware DLL，因此全新使用者仍須先執行下面的「本機建置」。若要發布已含原廠衍生資源的真正免準備一鍵包，應先取得適當的再散布授權。

### 由合法持有的來源在本機建置

準備：

- 自己合法取得的舊版 VMware 繁體中文語系目錄，壓縮成 `VM17_zh_TW.zip`，結構為 `zh_TW/{vmappsdk-zh_TW.dll,vmui-zh_TW.dll,vmware.vmsg}`。**檔案版本以 SHA-256 為準，ZIP 檔名本身不代表版本。**
- 已安裝 **VMware 26.0.1**，且原生 `messages\es` 尚未被修改；或自行取得對應版本的 ES 語系 ZIP。
- Python 3.10 或以上（僅**本機建置**需要；安裝器不需要 Python）。

將自己的 `VM17_zh_TW.zip` 放在專案根目錄，雙擊 **`Prepare-LocalPayload.cmd`**，或執行：

```powershell
py -3 builder\build_payload.py --old .\VM17_zh_TW.zip
```

若 26.0.1 的原始 ES 資源已被修改，可另外指定自己保存的原始 ZIP：

```powershell
py -3 builder\build_payload.py --old .\VM17_zh_TW.zip --new .\VM26H2_es.zip
```

建置器核對來源檔 SHA-256 與版本相容性、修正格式參數、保留 ES 資源識別碼、完成資源完整性驗證，最後將 v1.2 的三份檔案產生到 `payload\es`。來源不符就停止，不會猜測相容性。

建置完成後只需雙擊 `Install.cmd`。**不要把自己建置的 `payload` 內容公開上傳或併入 GitHub Release，除非具有必要授權。**

## 一鍵解除安裝／還原

關閉 VMware，雙擊 **`Uninstall.cmd`**。安裝器會確認檔案仍與 v1.2 相同，找到當時的可驗證備份，再還原原生 ES 或安裝前的版本，移除自己建立的桌面捷徑。備份目錄會保留在：

`%ProgramData%\VMware-Workstation-zh-TW-ES-Compat\Backups`

若從之前 v1.0 補丁升級，工具也會嘗試沿用原有 `%ProgramData%\VMware\LocalePatchBackups` 內的**原廠 ES 備份**。如果找不到原始檔、雜湊不符，會拒絕破壞性還原。

## 安裝器安全設計

- 僅適用指定 build，**嚴格檢查 3 份 DLL / VMSG 的 SHA-256**。
- 不終止 VMware、不修改虛擬機器檔案、不調整 Windows 防毒與執行原則的全域設定。
- 安裝前備份，寫入後再次驗證；中途錯誤嘗試自動回滾。
- 重複安裝 v1.2 不會重複覆蓋檔案，只驗證並建立捷徑。
- 啟動捷徑使用 `--locale=es`，不會更動使用者原有的 VMware 偏好設定。
- 任何修改過的語系 DLL 原始數位簽章不再有效，請自行評估安全政策；勿忽略 Windows 的安全警示。

## 已知限制

- 目前只測試 Windows / VMware 26.0.1；尚未針對其他版本驗收。
- 介面裡動態插入的 `Workstation 25H2 or later` 可能維持英文。
- 文字長度在不同 DPI、縮放設定或視窗尺寸可能不同；部分畫面尚待社群回報。
- 語系 DLL 為非官方修改檔，不代表 Broadcom 認可或提供技術支援。
- 本專案不提供 VMware 安裝程式、授權金鑰、DLL 下載來源或繞過原廠授權的功能。

## 開源與資源授權

原創的建置工具與安裝器採用 **MIT License**，只涵蓋這些原創程式碼。VMware、Workstation、Broadcom 及原廠 DLL、語系文字、商標等均為各權利人所有；詳見 [NOTICE.md](NOTICE.md)。**MIT 並不授權散布 VMware 專有資源。**

若要對外發布帶完整語系的安裝包，請先確認 Broadcom 授權或取得權利人同意。

## 專案內容

| 檔案 | 用途 |
|---|---|
| `Install.cmd` | 一鍵安裝與自動建立桌面捷徑 |
| `Uninstall.cmd` | 一鍵還原已驗證備份並移除捷徑 |
| `Prepare-LocalPayload.cmd` | 使用自己合法取得的舊版語系，在本機建置 |
| `scripts/LocaleInstaller.ps1` | UAC、版本驗證、SHA-256、備份/還原、桌面捷徑 |
| `builder/` | 資源解析、繁體中文合併與相容 PE 資源重建 |
| `payload/es/` | 使用者本機產物，不在 GitHub 追蹤 |
| `tests/` | 靜態與版本完整性測試 |

## 授權與聲明

本專案與 VMware/Broadcom 無關。來源資源與改寫後資源的使用、改作及散布均須遵守適用的原廠授權。請勿將此工具誤認為官方語言套件。