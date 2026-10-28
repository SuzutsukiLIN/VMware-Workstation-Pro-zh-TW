# 公開發布與授權檢查表

儲存庫：https://github.com/SuzutsukiLIN/VMware-Workstation-Pro-zh-TW

1. GitHub 提交與 Releases **只包含原創原始碼**。嚴禁上傳 VMware DLL、完整 .vmsg 或包含這些資料的 ZIP。
2. 發布前確認 payload/es 僅追蹤 .gitkeep。
3. 執行 GitHub Actions 的 Source-only validation，確認測試通過。
4. 在符合版本的 Windows 26.0.1 測試安裝／重複安裝／解除安裝／還原／桌面捷徑。
5. Release 可使用 GitHub 自動提供的 Source code ZIP，不另外加入修改後的 VMware DLL。
6. 若希望公開真正的「下載一次、安裝完成」完整語系套件，應先取得 Broadcom 對涉及原廠資源之再散布授權。

請不要把自己合法擁有的來源語系 ZIP 或建置後的 payload 加入公開 Git 版本歷史。即使日後刪除檔案，舊 Commit 也可能繼續含有內容。

## 公開版與私人驗收版的差異

公開版只能在本機從合法取得的來源建立語系資源；私人驗收版包含已建立的語系 DLL，不是公開發行檔案。README 需如實描述此差異。
