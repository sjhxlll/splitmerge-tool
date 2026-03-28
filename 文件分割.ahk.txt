; --------------------------------------------------------------------------------
; 脚本名称: AHK 文件分割神器 V5 (终极防屏蔽版)
; 语言: AutoHotkey V2.0+
; --------------------------------------------------------------------------------

#Requires AutoHotkey v2.0
#SingleInstance Force

; ==============================================================================
; 全局变量与 GUI
; ==============================================================================
MainGui := Gui(, "AHK 文件分割神器 - 终极防屏蔽版")
MainGui.OnEvent("Close", (*) => ExitApp())
MainGui.SetFont("s10", "Segoe UI")

MainGui.Add("GroupBox", "x10 y10 w400 h60", "第一步：拖入文件")
edtFilePath := MainGui.Add("Edit", "x20 y30 w380 h30 ReadOnly", "请将文件拖拽至此窗口...")

MainGui.Add("GroupBox", "x10 y80 w400 h60", "第二步：分割设置")
MainGui.Add("Text", "x20 y105", "大小(MB):")
edtSplitSize := MainGui.Add("Edit", "x85 y100 w50 Number", "100") 
MainGui.Add("UpDown", "Range1-20000", 100)

; 伪装后缀设置 (加回此处)
MainGui.Add("Text", "x150 y105", "伪装后缀:")
edtSuffix := MainGui.Add("Edit", "x215 y100 w50", ".pkg")
MainGui.Add("Text", "x270 y105 cBlue", "(自动生成随机文件名)")

progBar := MainGui.Add("Progress", "x10 y150 w400 h20 cGreen", 0)
btnSplit := MainGui.Add("Button", "x10 y180 w400 h40", "开始分割并生成合并器")
btnSplit.OnEvent("Click", StartSplitProcess)

MainGui.OnEvent("DropFiles", OnFileDrop)
MainGui.Show("w420 h240")

; ==============================================================================
; 事件与逻辑
; ==============================================================================

OnFileDrop(GuiObj, GuiCtrlObj, FileArray, X, Y) {
    if (FileArray.Length > 0)
        edtFilePath.Value := FileArray[1]
}

StartSplitProcess(*) {
    targetFile := edtFilePath.Value
    customSuffix := edtSuffix.Value
    
    if (targetFile = "" || targetFile = "请将文件拖拽至此窗口...") {
        MsgBox("请先拖入文件！", "错误", "Icon!")
        return
    }
    if (!FileExist(targetFile)) {
        MsgBox("文件不存在。", "错误", "Icon!")
        return
    }

    ; 处理后缀的小数点
    if (customSuffix != "" && SubStr(customSuffix, 1, 1) != ".")
        customSuffix := "." customSuffix

    chunkSizeMB := Integer(edtSplitSize.Value)
    if (chunkSizeMB <= 0) {
        MsgBox("分块大小错误。", "错误", "Icon!")
        return
    }

    btnSplit.Enabled := false
    ; 将后缀参数传递给分割函数
    SplitFileRandomly(targetFile, chunkSizeMB, customSuffix)
    btnSplit.Enabled := true
}

SplitFileRandomly(sourcePath, sizeMB, suffix) {
    try {
        fSource := FileOpen(sourcePath, "r")
    } catch as err {
        MsgBox("无法打开: " err.Message)
        return
    }

    sourceSize := fSource.Length
    chunkSizeBytes := sizeMB * 1024 * 1024
    totalParts := Ceil(sourceSize / chunkSizeBytes)

    SplitPath(sourcePath, &outFileName, &outDir, &outExt, &outNameNoExt)
    outputDir := outDir "\" outNameNoExt "_parts"
    if (!DirExist(outputDir))
        DirCreate(outputDir)

    if (MsgBox("将生成 " totalParts " 个带 [" suffix "] 后缀的随机文件。``n确定继续吗？", "确认", "YesNo Icon?") == "No") {
        fSource.Close()
        return
    }

    bufferSize := 1024 * 1024 
    buf := Buffer(bufferSize)
    fileMapping := [] 

    Loop totalParts {
        ; 生成随机字符串，并直接拼接上用户设定的后缀
        randomName := GenerateRandomString(8) suffix
        partPath := outputDir "\" randomName
        
        fileMapping.Push(randomName)

        try {
            fDest := FileOpen(partPath, "w")
        } catch {
            MsgBox("创建失败: " partPath)
            break
        }

        bytesLeft := chunkSizeBytes
        while (bytesLeft > 0 && fSource.Pos < sourceSize) {
            readSize := Min(bufferSize, bytesLeft)
            readSize := Min(readSize, sourceSize - fSource.Pos)
            if (readSize <= 0) 
                break
            bytesRead := fSource.RawRead(buf, readSize)
            fDest.RawWrite(buf, bytesRead)
            bytesLeft -= bytesRead
        }
        fDest.Close()
        progBar.Value := (A_Index / totalParts) * 100
    }
    fSource.Close()

    mappingStr := "["
    for index, name in fileMapping {
        mappingStr .= '"' name '"' (index < fileMapping.Length ? ", " : "")
    }
    mappingStr .= "]"

    GenerateMergerScript(outputDir, outFileName, mappingStr)
    
    MsgBox("分割完成！``n文件已保存在: " outputDir, "成功", "Iconi")
    try {
        Run(outputDir)
    }
}

GenerateRandomString(length) {
    chars := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    str := ""
    Loop length {
        rand := Random(1, StrLen(chars))
        str .= SubStr(chars, rand, 1)
    }
    return str
}

; ==============================================================================
; 生成合并器
; ==============================================================================

GenerateMergerScript(saveDir, originalName, mappingString) {
    mergerScriptContent := "
    (
    #Requires AutoHotkey v2.0
    #SingleInstance Force

    Global TargetFileName := "{1}"
    Global PartsList := {2} 

    MainGui := Gui(, "文件还原工具 - " TargetFileName)
    MainGui.OnEvent("Close", (*) => ExitApp())
    MainGui.SetFont("s9", "Segoe UI")

    MainGui.Add("Text", "x10 y10 w400", "目标还原: " TargetFileName)
    MainGui.Add("Text",, "已内置混淆文件映射表，自动精准匹配。")

    Global lstStatus := MainGui.Add("ListView", "x10 y60 w480 h200 Grid", ["序号", "对应文件名", "状态"])
    lstStatus.ModifyCol(1, 40)
    lstStatus.ModifyCol(2, 300)
    lstStatus.ModifyCol(3, 100)

    Global btnMerge := MainGui.Add("Button", "x10 y270 w480 h40 Disabled", "正在扫描...")
    btnMerge.OnEvent("Click", StartMerge)

    MainGui.Show("w500 h330")

    SetTimer(CheckParts, 1000)
    CheckParts()

    CheckParts() {
        foundCount := 0
        lstStatus.Delete()
        
        for index, fileName in PartsList {
            status := "❌ 缺失"
            if FileExist(A_ScriptDir "\" fileName) {
                status := "✅ 就绪"
                foundCount++
            }
            lstStatus.Add(, index, fileName, status)
        }

        if (foundCount == PartsList.Length) {
            btnMerge.Text := "文件完整 - 点击合并"
            btnMerge.Enabled := true
        } else {
            btnMerge.Text := "缺少文件 (" foundCount "/" PartsList.Length ")..."
            btnMerge.Enabled := false
        }
    }

    StartMerge(*) {
        if FileExist(TargetFileName) {
            if (MsgBox("文件已存在，是否覆盖？", "警告", "YesNo Icon!") = "No")
                return
            FileDelete(TargetFileName)
        }

        btnMerge.Enabled := false
        btnMerge.Text := "正在合并..."
        
        try {
            fOut := FileOpen(TargetFileName, "w")
            buf := Buffer(1024 * 1024)
            
            for index, fileName in PartsList {
                partPath := A_ScriptDir "\" fileName
                fPart := FileOpen(partPath, "r")
                fPartLen := fPart.Length
                while (fPart.Pos < fPartLen) {
                    readBytes := fPart.RawRead(buf, buf.Size)
                    fOut.RawWrite(buf, readBytes)
                }
                fPart.Close()
            }
            fOut.Close()
            MsgBox("合并成功！``n文件: " TargetFileName, "成功")
            ExitApp()
        } catch as err {
            MsgBox("错误: " err.Message)
            btnMerge.Enabled := true
        }
    }
    )"
    
    finalScript := Format(mergerScriptContent, originalName, mappingString)
    scriptPath := saveDir "\合并_" originalName ".ahk"
    
    try {
        if FileExist(scriptPath)
            FileDelete(scriptPath)
        FileAppend(finalScript, scriptPath, "UTF-8")
    }

    compilerPath := RegRead("HKEY_LOCAL_MACHINE\SOFTWARE\AutoHotkey", "InstallDir", "") "\Compiler\Ahk2Exe.exe"
    if (compilerPath != "" && FileExist(compilerPath)) {
        exePath := StrReplace(scriptPath, ".ahk", ".exe")
        try {
            RunWait('"' compilerPath '" /in "' scriptPath '" /out "' exePath '"')
            FileDelete(scriptPath)
        }
    }
}