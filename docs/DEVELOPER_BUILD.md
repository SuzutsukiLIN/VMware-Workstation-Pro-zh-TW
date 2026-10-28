# 開發者：使用自有來源檔重建翻譯資源

> 本頁是開發者 / 維護者的重現流程，**不是一般使用者的安裝步驟**。公開原始碼目前不提供可直接使用的繁體中文資源。

## 必要檔案

1. 自行合法取得的舊版 VMware 繁中語系檔，整理成 `zh_TW/vmappsdk-zh_TW.dll`、`zh_TW/vmui-zh_TW.dll`、`zh_TW/vmware.vmsg`，再壓縮為 `VM17_zh_TW.zip`。壓縮檔名只是建置工具使用的名稱，**不代表真實檔案版本**；工具會比對內容雜湊。
2. 已安裝 VMware Workstation 26.0.1 build-25688693，且原生 `messages\es` 未被修改；或自行保存相同版本的 `es` 語系 ZIP。
3. Python 3.10+（只有開發者建置需要）。

## 重建流程

在專案根目錄執行：

```powershell
py -3 builder\build_payload.py --old .\VM17_zh_TW.zip
```

若目前 VMware 原生 ES 語系已被修改，可指定自己備份的原廠版本：

```powershell
py -3 builder\build_payload.py --old .\VM17_zh_TW.zip --new .\VM26H2_es.zip
```

程式會比對原始來源 SHA-256、合併訊息及 Win32 對話框資源，驗證後輸出三件套至 `payload\es`。只有檢查成功時才應執行 `Install.cmd`；來源雜湊或版本不同時不會猜測相容性。

**請勿把自行重建的 VMware 衍生 DLL / VMSG 直接上傳到 GitHub 或附加到 Release，除非已取得必要授權。** 

## 產品方向

目標是讓一般使用者無需上述壓縮檔或 Python：直接從已安裝的 VMware 26.0.1 原生 ES 資源，在本機套用可合法散布的翻譯修補資料並建立桌面捷徑。

在該資料的授權、Windows 實機首次安裝與還原都完成驗證前，不應宣稱公開版已達成真正的免準備一鍵安裝。
