# splitmerge-tool

## 已实现内容

- Windows 桌面版脚本: `splitmerge_gui.ahk`
  - 固定输出 `.pkg` 分块
  - 分割单位支持 `KB` / `MB`
  - 生成 `manifest.json`
  - 自动生成一键检测+合并程序（`合并_原文件名.ahk`，若本机有 Ahk2Exe 则自动编译为 `.exe`）
  - 检测支持缺失与 SHA-256 校验

- 浏览器本地版: `splitmerge_web.html`
  - Split 模式：分割并生成 `.pkg`、`manifest.json`、`merge-program.html`
  - Merge 模式：加载 `manifest.json` 与 `.pkg` 文件，先检测再一键合并
  - 检测支持缺失与 SHA-256 校验

## 使用方法

1. 安装 AutoHotkey v2 后运行 `splitmerge_gui.ahk`。
2. 拖入文件，选择分割大小和单位，点击“开始分割并生成一键合并器”。
3. 在输出目录可看到所有 `.pkg`、`manifest.json` 与合并程序。
4. 若输出的是 `.ahk` 合并脚本，可直接运行；若自动编译成功会得到 `.exe`。

## 浏览器方案

1. 双击打开 `splitmerge_web.html`。
2. 在“分割”页选择源文件、分割大小与单位后开始分割。
3. 下载页面列出的所有文件（含 `merge-program.html`）。
4. 双击 `merge-program.html`，选中全部 `.pkg`，点击检测后即可一键合并。

## 注意事项

- SHA-256 使用系统/浏览器能力计算，首次大文件检测耗时较长属正常现象。
- 浏览器页面无文件系统写权限，分块文件需手动点击下载保存。
- 建议分割大小 >= 1 MB，可明显减少分块数量。
