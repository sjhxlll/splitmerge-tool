#Requires AutoHotkey v2.0
#SingleInstance Force

; =========================
; GUI
; =========================
MainGui := Gui(, "文件分割与合并工具")
MainGui.OnEvent("Close", (*) => ExitApp())
MainGui.SetFont("s10", "Segoe UI")

MainGui.Add("GroupBox", "x10 y10 w520 h70", "第一步：拖入文件")
edtFilePath := MainGui.Add("Edit", "x20 y35 w500 h30 ReadOnly", "请将文件拖拽到窗口...")

MainGui.Add("GroupBox", "x10 y90 w520 h90", "第二步：分割设置")
MainGui.Add("Text", "x20 y118", "分割大小:")
edtSplitSize := MainGui.Add("Edit", "x90 y113 w80 Number", "100")
MainGui.Add("UpDown", "Range1-500000", 100)
MainGui.Add("Text", "x180 y118", "单位:")
ddlUnit := MainGui.Add("DropDownList", "x220 y113 w80 Choose2", ["KB", "MB"])
MainGui.Add("Text", "x320 y118", "后缀:")
MainGui.Add("Edit", "x360 y113 w70 ReadOnly", ".pkg")
MainGui.Add("Text", "x440 y118 cBlue", "(固定)")

lblStatus := MainGui.Add("Text", "x10 y188 w520", "状态：待开始")
progBar := MainGui.Add("Progress", "x10 y210 w520 h20 cGreen", 0)
btnSplit := MainGui.Add("Button", "x10 y240 w520 h45", "开始分割并生成一键合并器")
btnSplit.OnEvent("Click", StartSplitProcess)

MainGui.OnEvent("DropFiles", OnFileDrop)
MainGui.Show("w540 h300")

OnFileDrop(GuiObj, GuiCtrlObj, FileArray, X, Y) {
    if (FileArray.Length > 0)
        edtFilePath.Value := FileArray[1]
}

StartSplitProcess(*) {
    targetFile := Trim(edtFilePath.Value)
    sizeValue := Integer(edtSplitSize.Value)
    unit := ddlUnit.Text

    if (targetFile = "" || targetFile = "请将文件拖拽到窗口...") {
        MsgBox("请先拖入文件。", "错误", "Icon!")
        return
    }
    if (!FileExist(targetFile)) {
        MsgBox("文件不存在。", "错误", "Icon!")
        return
    }
    if (sizeValue <= 0) {
        MsgBox("分割大小必须大于 0。", "错误", "Icon!")
        return
    }

    chunkSizeBytes := (unit = "KB") ? (sizeValue * 1024) : (sizeValue * 1024 * 1024)
    if (chunkSizeBytes < 1024) {
        MsgBox("分割大小过小，至少 1 KB。", "错误", "Icon!")
        return
    }

    btnSplit.Enabled := false
    progBar.Value := 0
    lblStatus.Text := "状态：正在准备..."

    ok := SplitFileToPkg(targetFile, sizeValue, unit, chunkSizeBytes)

    btnSplit.Enabled := true
    if (!ok)
        lblStatus.Text := "状态：失败"
}

SplitFileToPkg(sourcePath, sizeValue, unit, chunkSizeBytes) {
    try {
        fSource := FileOpen(sourcePath, "r")
    } catch as err {
        MsgBox("无法打开源文件：" err.Message, "错误", "Icon!")
        return false
    }

    sourceSize := fSource.Length
    if (sourceSize = 0) {
        fSource.Close()
        MsgBox("源文件为空，无法分割。", "错误", "Icon!")
        return false
    }

    totalParts := Ceil(sourceSize / chunkSizeBytes)
    SplitPath(sourcePath, &outFileName, &outDir, &outExt, &outNameNoExt)
    outputDir := outDir "\" outNameNoExt "_pkg_parts"

    if (!DirExist(outputDir))
        DirCreate(outputDir)

    if (MsgBox(
        "将生成 " totalParts " 个 .pkg 分块。`n"
        . "分割大小：" sizeValue " " unit "`n"
        . "输出目录：" outputDir "`n`n继续吗？",
        "确认",
        "YesNo Icon?"
    ) = "No") {
        fSource.Close()
        return false
    }

    bufferSize := 4 * 1024 * 1024
    buf := Buffer(bufferSize)
    parts := []

    Loop totalParts {
        idx := A_Index
        partName := Format("part_{:05}.pkg", idx)
        partPath := outputDir "\" partName

        try {
            fDest := FileOpen(partPath, "w")
        } catch as err {
            fSource.Close()
            MsgBox("无法创建分块文件：" partPath "`n" err.Message, "错误", "Icon!")
            return false
        }

        bytesLeft := chunkSizeBytes
        bytesWritten := 0

        while (bytesLeft > 0 && fSource.Pos < sourceSize) {
            readSize := Min(bufferSize, bytesLeft)
            readSize := Min(readSize, sourceSize - fSource.Pos)
            if (readSize <= 0)
                break

            bytesRead := fSource.RawRead(buf, readSize)
            if (bytesRead <= 0)
                break

            fDest.RawWrite(buf, bytesRead)
            bytesLeft -= bytesRead
            bytesWritten += bytesRead
        }
        fDest.Close()

        partHash := GetFileSHA256(partPath)
        if (partHash = "") {
            fSource.Close()
            MsgBox("无法计算分块哈希：" partName, "错误", "Icon!")
            return false
        }

        parts.Push({
            Name: partName,
            Size: bytesWritten,
            Hash: partHash
        })

        progBar.Value := Round((idx / totalParts) * 100)
        lblStatus.Text := "状态：已生成 " idx "/" totalParts " 个分块"
    }

    fSource.Close()

    sourceHash := GetFileSHA256(sourcePath)
    if (sourceHash = "") {
        MsgBox("无法计算源文件 SHA-256。", "错误", "Icon!")
        return false
    }

    manifestPath := outputDir "\manifest.json"
    if (!WriteManifest(manifestPath, outFileName, sourceSize, sourceHash, sizeValue, unit, chunkSizeBytes, parts)) {
        MsgBox("manifest.json 生成失败。", "错误", "Icon!")
        return false
    }

    namesArrayStr := BuildArrayString(parts, "Name")
    hashArrayStr := BuildArrayString(parts, "Hash")
    sizeArrayStr := BuildNumberArrayString(parts, "Size")

    GenerateMergerScript(outputDir, outFileName, namesArrayStr, hashArrayStr, sizeArrayStr, sourceHash, sourceSize)

    progBar.Value := 100
    lblStatus.Text := "状态：完成"
    MsgBox("分割完成。`n输出目录：" outputDir "`n已生成：manifest.json 与一键合并器", "成功", "Iconi")

    try {
        Run(outputDir)
    }

    return true
}

WriteManifest(path, originalName, originalSize, originalHash, sizeValue, unit, chunkSizeBytes, parts) {
    partRows := ""
    for idx, p in parts {
        row := "    {" 
            . '"index":' idx ","
            . '"name":"' JsonEscape(p.Name) '",'
            . '"size":' p.Size ","
            . '"sha256":"' p.Hash '"'
            . "}"
        if (idx < parts.Length)
            row .= ","
        partRows .= row "`n"
    }

    json := "{" "`n"
        . '  "version":1,' "`n"
        . '  "originalName":"' JsonEscape(originalName) '",' "`n"
        . '  "originalSize":' originalSize "," "`n"
        . '  "originalSha256":"' originalHash '",' "`n"
        . '  "chunkValue":' sizeValue "," "`n"
        . '  "chunkUnit":"' unit '",' "`n"
        . '  "chunkBytes":' chunkSizeBytes "," "`n"
        . '  "parts":[' "`n"
        . partRows
        . "  ]`n"
        . "}`n"

    try {
        if (FileExist(path))
            FileDelete(path)
        FileAppend(json, path, "UTF-8")
        return true
    } catch {
        return false
    }
}

BuildArrayString(parts, key) {
    out := "["
    for idx, p in parts {
        out .= '"' p.%key% '"'
        if (idx < parts.Length)
            out .= ","
    }
    out .= "]"
    return out
}

BuildNumberArrayString(parts, key) {
    out := "["
    for idx, p in parts {
        out .= p.%key%
        if (idx < parts.Length)
            out .= ","
    }
    out .= "]"
    return out
}

JsonEscape(value) {
    v := StrReplace(value, "\\", "\\\\")
    v := StrReplace(v, '"', '\"')
    v := StrReplace(v, "`r", "")
    v := StrReplace(v, "`n", "\n")
    return v
}

GetFileSHA256(path) {
    if (!FileExist(path))
        return ""

    tmpOut := A_Temp "\\sha256_" A_TickCount "_" Random(1000, 9999) ".txt"
    cmd := A_ComSpec ' /C certutil -hashfile "' path '" SHA256 > "' tmpOut '"'
    code := RunWait(cmd, , "Hide")
    if (code != 0 || !FileExist(tmpOut))
        return ""

    try {
        content := FileRead(tmpOut, "UTF-8")
    } catch {
        try content := FileRead(tmpOut)
    }

    try FileDelete(tmpOut)

    ; certutil 输出一般第二行是哈希值，包含空格分隔。
    lines := StrSplit(content, "`n", "`r")
    for _, line in lines {
        s := Trim(line)
        if (RegExMatch(s, "i)^[0-9a-f ]{64,}$")) {
            s := StrReplace(s, " ")
            return StrUpper(s)
        }
    }
    return ""
}

GenerateMergerScript(saveDir, originalName, namesArrayStr, hashArrayStr, sizeArrayStr, sourceHash, sourceSize) {
    mergerScriptContent :=
    (
    #Requires AutoHotkey v2.0
    #SingleInstance Force

    Global TargetFileName := "{1}"
    Global TargetFileHash := "{2}"
    Global TargetFileSize := {3}
    Global PartNames := {4}
    Global PartHashes := {5}
    Global PartSizes := {6}

    MainGui := Gui(, "一键合并器 - " TargetFileName)
    MainGui.OnEvent("Close", (*) => ExitApp())
    MainGui.SetFont("s9", "Segoe UI")

    MainGui.Add("Text", "x10 y10 w580", "目标文件: " TargetFileName)
    MainGui.Add("Text", "x10 y30 w580", "SHA-256: " TargetFileHash)

    Global lstStatus := MainGui.Add("ListView", "x10 y55 w580 h240 Grid", ["序号", "分块文件", "状态"])
    lstStatus.ModifyCol(1, 50)
    lstStatus.ModifyCol(2, 280)
    lstStatus.ModifyCol(3, 220)

    Global btnCheck := MainGui.Add("Button", "x10 y305 w285 h40", "重新检测")
    Global btnMerge := MainGui.Add("Button", "x305 y305 w285 h40 Disabled", "一键合并")
    btnCheck.OnEvent("Click", CheckParts)
    btnMerge.OnEvent("Click", StartMerge)

    MainGui.Show("w600 h360")
    CheckParts()

    CheckParts(*) {
        foundCount := 0
        okCount := 0
        lstStatus.Delete()

        for idx, partName in PartNames {
            partPath := A_ScriptDir "\" partName
            status := "缺失"

            if (FileExist(partPath)) {
                foundCount++
                hash := GetFileSHA256(partPath)
                size := FileGetSize(partPath)
                if (hash = PartHashes[idx] && size = PartSizes[idx]) {
                    status := "完整"
                    okCount++
                } else {
                    status := "损坏(哈希或大小不匹配)"
                }
            }

            lstStatus.Add(, idx, partName, status)
        }

        if (okCount = PartNames.Length) {
            btnMerge.Text := "文件完整 - 点击一键合并"
            btnMerge.Enabled := true
        } else {
            btnMerge.Text := "未就绪: 完整 " okCount " / " PartNames.Length
            btnMerge.Enabled := false
        }
    }

    StartMerge(*) {
        CheckParts()
        if (!btnMerge.Enabled) {
            MsgBox("存在缺失或损坏分块，无法合并。", "提示", "Icon!")
            return
        }

        if FileExist(TargetFileName) {
            if (MsgBox("目标文件已存在，是否覆盖？", "警告", "YesNo Icon!") = "No")
                return
            FileDelete(TargetFileName)
        }

        btnMerge.Enabled := false
        btnMerge.Text := "正在合并..."

        try {
            fOut := FileOpen(TargetFileName, "w")
            buf := Buffer(4 * 1024 * 1024)

            for idx, partName in PartNames {
                partPath := A_ScriptDir "\" partName
                fPart := FileOpen(partPath, "r")
                while (fPart.Pos < fPart.Length) {
                    readBytes := fPart.RawRead(buf, buf.Size)
                    if (readBytes <= 0)
                        break
                    fOut.RawWrite(buf, readBytes)
                }
                fPart.Close()
            }

            fOut.Close()

            mergedHash := GetFileSHA256(TargetFileName)
            mergedSize := FileGetSize(TargetFileName)
            if (mergedHash != TargetFileHash || mergedSize != TargetFileSize) {
                MsgBox("合并完成，但校验失败。`n请重新检查分块文件。", "错误", "Icon!")
                btnMerge.Enabled := true
                btnMerge.Text := "一键合并"
                return
            }

            MsgBox("合并成功并通过校验。`n文件: " TargetFileName, "成功", "Iconi")
            ExitApp()
        } catch as err {
            MsgBox("合并失败: " err.Message, "错误", "Icon!")
            btnMerge.Enabled := true
            btnMerge.Text := "一键合并"
        }
    }

    GetFileSHA256(path) {
        tmpOut := A_Temp "\sha256_merge_" A_TickCount "_" Random(1000, 9999) ".txt"
        cmd := A_ComSpec ' /C certutil -hashfile "' path '" SHA256 > "' tmpOut '"'
        code := RunWait(cmd, , "Hide")
        if (code != 0 || !FileExist(tmpOut))
            return ""

        try {
            content := FileRead(tmpOut, "UTF-8")
        } catch {
            content := FileRead(tmpOut)
        }
        try FileDelete(tmpOut)

        lines := StrSplit(content, "`n", "`r")
        for _, line in lines {
            s := Trim(line)
            if (RegExMatch(s, "i)^[0-9a-f ]{64,}$")) {
                s := StrReplace(s, " ")
                return StrUpper(s)
            }
        }
        return ""
    }
    )

    finalScript := Format(
        mergerScriptContent,
        originalName,
        sourceHash,
        sourceSize,
        namesArrayStr,
        hashArrayStr,
        sizeArrayStr
    )

    scriptPath := saveDir "\\合并_" originalName ".ahk"

    try {
        if (FileExist(scriptPath))
            FileDelete(scriptPath)
        FileAppend(finalScript, scriptPath, "UTF-8")
    } catch as err {
        MsgBox("生成合并脚本失败：" err.Message, "错误", "Icon!")
        return
    }

    compilerPath := RegRead("HKEY_LOCAL_MACHINE\\SOFTWARE\\AutoHotkey", "InstallDir", "") "\\Compiler\\Ahk2Exe.exe"
    if (compilerPath != "" && FileExist(compilerPath)) {
        exePath := StrReplace(scriptPath, ".ahk", ".exe")
        try {
            RunWait('"' compilerPath '" /in "' scriptPath '" /out "' exePath '"', , "Hide")
            if (FileExist(exePath))
                FileDelete(scriptPath)
        }
    }
}
