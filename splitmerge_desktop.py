import hashlib
import json
import os
import random
import shutil
import string
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def safe_base_name(name: str) -> str:
    stem = Path(name).stem
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in stem).strip("_")
    return cleaned or "file"


def random_id(length: int = 10) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def bytes_from_unit(value: int, unit: str) -> int:
    if unit == "KB":
        return value * 1024
    if unit == "MB":
        return value * 1024 * 1024
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class SplitMergeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.lang = "zh"
        self.root.title("文件拆分合并工具")
        self.root.geometry("860x620")
        self.root.minsize(760, 520)

        self.i18n = {
            "zh": {
                "title": "文件拆分合并工具",
                "lang_btn": "English",
                "tab_split": "切分",
                "tab_merge": "合并",
                "source_file": "源文件",
                "browse": "浏览",
                "chunk_size": "分片大小",
                "output_name": "合并输出文件名（可选）",
                "prefix_name": "分片文件名前缀（可选）",
                "random_prefix": "使用随机分片前缀",
                "random_each": "每个分片使用随机文件名",
                "release_program": "切分后自动释放主程序到输出文件夹",
                "start_split": "开始切分",
                "ready": "就绪。",
                "waiting_input": "等待输入。",
                "manifest_file": "清单文件 (.manifest.pkg.json)",
                "chunk_folder": "分片文件夹",
                "verify": "校验",
                "merge": "合并",
                "choose_manifest": "请选择清单和分片目录。",
                "select_source": "选择源文件",
                "select_manifest": "选择清单文件",
                "select_chunk_folder": "选择分片目录",
                "invalid_source": "请选择有效的源文件。",
                "invalid_size": "分片大小必须是正整数。",
                "splitting": "切分中...",
                "output_folder": "输出文件夹",
                "split_done": "切分完成。",
                "split_failed": "切分失败。",
                "manifest_saved": "清单文件",
                "done": "完成",
                "split_completed": "切分完成。\n输出目录：\n{path}",
                "verify_start": "校验中...",
                "verify_failed": "校验失败。",
                "verify_passed": "校验通过。",
                "verify_error": "校验异常。",
                "merge_start": "合并中...",
                "merge_done": "合并完成。",
                "merge_failed": "合并失败。",
                "merge_completed": "合并完成。\n输出文件：\n{path}",
                "manifest_invalid": "清单文件无效。",
                "chunk_folder_invalid": "分片目录无效。",
                "expected_chunks": "期望分片数",
                "missing": "缺失",
                "hash_mismatch": "哈希不匹配",
                "none": "无",
                "extra_ignored": "额外 .pkg（已忽略）",
                "merged_file": "合并输出",
                "missing_chunk": "缺少分片",
                "hash_bad": "分片哈希不匹配",
                "releasing_program": "正在释放主程序",
                "release_program_done": "已释放主程序",
                "release_program_failed": "释放主程序失败",
                "released_bat": "已生成启动脚本",
                "merged_line": "[{idx}/{total}] 已合并 {name}",
                "split_line": "[{idx}/{total}] {name} ({size} bytes)",
            },
            "en": {
                "title": "SplitMerge Desktop Tool",
                "lang_btn": "中文",
                "tab_split": "Split",
                "tab_merge": "Merge",
                "source_file": "Source file",
                "browse": "Browse",
                "chunk_size": "Chunk size",
                "output_name": "Merged output filename (optional)",
                "prefix_name": "Chunk filename prefix (optional)",
                "random_prefix": "Use random chunk prefix",
                "random_each": "Use random name for each chunk",
                "release_program": "Auto release main app to output folder after split",
                "start_split": "Start Split",
                "ready": "Ready.",
                "waiting_input": "Waiting for input.",
                "manifest_file": "Manifest file (.manifest.pkg.json)",
                "chunk_folder": "Chunk folder",
                "verify": "Verify",
                "merge": "Merge",
                "choose_manifest": "Choose manifest and chunk folder.",
                "select_source": "Select source file",
                "select_manifest": "Select manifest file",
                "select_chunk_folder": "Select chunk folder",
                "invalid_source": "Please select a valid source file.",
                "invalid_size": "Chunk size must be a positive integer.",
                "splitting": "Splitting...",
                "output_folder": "Output folder",
                "split_done": "Split done.",
                "split_failed": "Split failed.",
                "manifest_saved": "Manifest",
                "done": "Done",
                "split_completed": "Split completed.\nOutput folder:\n{path}",
                "verify_start": "Verifying...",
                "verify_failed": "Verification failed.",
                "verify_passed": "Verification passed.",
                "verify_error": "Verify failed.",
                "merge_start": "Merging...",
                "merge_done": "Merge done.",
                "merge_failed": "Merge failed.",
                "merge_completed": "Merge completed.\nOutput file:\n{path}",
                "manifest_invalid": "Manifest file is invalid.",
                "chunk_folder_invalid": "Chunk folder is invalid.",
                "expected_chunks": "Expected chunks",
                "missing": "Missing",
                "hash_mismatch": "Hash mismatch",
                "none": "None",
                "extra_ignored": "Extra .pkg files (ignored)",
                "merged_file": "Merged file",
                "missing_chunk": "Missing chunk",
                "hash_bad": "Hash mismatch",
                "releasing_program": "Releasing main app",
                "release_program_done": "Main app released",
                "release_program_failed": "Failed to release main app",
                "released_bat": "Launcher script generated",
                "merged_line": "[{idx}/{total}] merged {name}",
                "split_line": "[{idx}/{total}] {name} ({size} bytes)",
            },
        }

        self._build_ui()
        self.apply_language()

    def tr(self, key: str, **kwargs) -> str:
        text = self.i18n.get(self.lang, {}).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

    def toggle_language(self) -> None:
        self.lang = "en" if self.lang == "zh" else "zh"
        self.apply_language()

    def apply_language(self) -> None:
        self.root.title(self.tr("title"))
        self.lang_btn.configure(text=self.tr("lang_btn"))
        self.notebook.tab(self.split_frame, text=self.tr("tab_split"))
        self.notebook.tab(self.merge_frame, text=self.tr("tab_merge"))

        self.source_label.configure(text=self.tr("source_file"))
        self.source_browse_btn.configure(text=self.tr("browse"))
        self.chunk_size_label.configure(text=self.tr("chunk_size"))
        self.output_name_label.configure(text=self.tr("output_name"))
        self.prefix_name_label.configure(text=self.tr("prefix_name"))
        self.random_prefix_chk.configure(text=self.tr("random_prefix"))
        self.random_each_chk.configure(text=self.tr("random_each"))
        self.release_program_chk.configure(text=self.tr("release_program"))
        self.start_split_btn.configure(text=self.tr("start_split"))

        self.manifest_label.configure(text=self.tr("manifest_file"))
        self.manifest_browse_btn.configure(text=self.tr("browse"))
        self.chunks_label.configure(text=self.tr("chunk_folder"))
        self.chunks_browse_btn.configure(text=self.tr("browse"))
        self.verify_btn.configure(text=self.tr("verify"))
        self.merge_btn.configure(text=self.tr("merge"))

        if self.split_status_var.get() in ("Ready.", "就绪。"):
            self.split_status_var.set(self.tr("ready"))
        if self.merge_status_var.get() in ("Ready.", "就绪。"):
            self.merge_status_var.set(self.tr("ready"))

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(10, 0))
        self.lang_btn = ttk.Button(top, text="English", command=self.toggle_language)
        self.lang_btn.pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.split_frame = ttk.Frame(self.notebook)
        self.merge_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.split_frame, text="Split")
        self.notebook.add(self.merge_frame, text="Merge")

        self._build_split_tab(self.split_frame)
        self._build_merge_tab(self.merge_frame)

    def _build_split_tab(self, parent: ttk.Frame) -> None:
        pad = {"padx": 8, "pady": 6}

        self.source_var = tk.StringVar()
        self.chunk_size_var = tk.StringVar(value="10")
        self.chunk_unit_var = tk.StringVar(value="MB")
        self.output_name_var = tk.StringVar()
        self.prefix_name_var = tk.StringVar()
        self.random_prefix_var = tk.BooleanVar(value=False)
        self.random_each_var = tk.BooleanVar(value=False)
        self.release_program_var = tk.BooleanVar(value=True)

        row = 0
        self.source_label = ttk.Label(parent, text="Source file")
        self.source_label.grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.source_var, width=80).grid(row=row, column=1, sticky="ew", **pad)
        self.source_browse_btn = ttk.Button(parent, text="Browse", command=self.select_source_file)
        self.source_browse_btn.grid(row=row, column=2, **pad)

        row += 1
        self.chunk_size_label = ttk.Label(parent, text="Chunk size")
        self.chunk_size_label.grid(row=row, column=0, sticky="w", **pad)
        size_wrap = ttk.Frame(parent)
        size_wrap.grid(row=row, column=1, sticky="w", **pad)
        ttk.Entry(size_wrap, textvariable=self.chunk_size_var, width=16).pack(side="left")
        ttk.Combobox(size_wrap, textvariable=self.chunk_unit_var, values=["KB", "MB"], width=6, state="readonly").pack(side="left", padx=6)

        row += 1
        self.output_name_label = ttk.Label(parent, text="Merged output filename (optional)")
        self.output_name_label.grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.output_name_var, width=80).grid(row=row, column=1, columnspan=2, sticky="ew", **pad)

        row += 1
        self.prefix_name_label = ttk.Label(parent, text="Chunk filename prefix (optional)")
        self.prefix_name_label.grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.prefix_name_var, width=80).grid(row=row, column=1, columnspan=2, sticky="ew", **pad)

        row += 1
        checks_wrap = ttk.Frame(parent)
        checks_wrap.grid(row=row, column=1, columnspan=2, sticky="w", **pad)
        self.random_prefix_chk = ttk.Checkbutton(checks_wrap, text="Use random chunk prefix", variable=self.random_prefix_var)
        self.random_prefix_chk.pack(anchor="w")
        self.random_each_chk = ttk.Checkbutton(checks_wrap, text="Use random name for each chunk", variable=self.random_each_var)
        self.random_each_chk.pack(anchor="w")
        self.release_program_chk = ttk.Checkbutton(
            checks_wrap,
            text="Auto release main app to output folder after split",
            variable=self.release_program_var,
        )
        self.release_program_chk.pack(anchor="w")

        row += 1
        action_wrap = ttk.Frame(parent)
        action_wrap.grid(row=row, column=1, columnspan=2, sticky="w", **pad)
        self.start_split_btn = ttk.Button(action_wrap, text="Start Split", command=self.start_split)
        self.start_split_btn.pack(side="left")

        row += 1
        self.split_status_var = tk.StringVar(value=self.tr("ready"))
        ttk.Label(parent, textvariable=self.split_status_var).grid(row=row, column=0, columnspan=3, sticky="w", **pad)

        row += 1
        self.split_log = tk.Text(parent, height=18)
        self.split_log.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        self.split_log.insert("1.0", self.tr("waiting_input") + "\n")
        self.split_log.configure(state="disabled")

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

    def _build_merge_tab(self, parent: ttk.Frame) -> None:
        pad = {"padx": 8, "pady": 6}

        self.manifest_var = tk.StringVar()
        self.chunks_dir_var = tk.StringVar()

        row = 0
        self.manifest_label = ttk.Label(parent, text="Manifest file (.manifest.pkg.json)")
        self.manifest_label.grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.manifest_var, width=80).grid(row=row, column=1, sticky="ew", **pad)
        self.manifest_browse_btn = ttk.Button(parent, text="Browse", command=self.select_manifest_file)
        self.manifest_browse_btn.grid(row=row, column=2, **pad)

        row += 1
        self.chunks_label = ttk.Label(parent, text="Chunk folder")
        self.chunks_label.grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.chunks_dir_var, width=80).grid(row=row, column=1, sticky="ew", **pad)
        self.chunks_browse_btn = ttk.Button(parent, text="Browse", command=self.select_chunks_dir)
        self.chunks_browse_btn.grid(row=row, column=2, **pad)

        row += 1
        action_wrap = ttk.Frame(parent)
        action_wrap.grid(row=row, column=1, columnspan=2, sticky="w", **pad)
        self.verify_btn = ttk.Button(action_wrap, text="Verify", command=self.start_verify)
        self.verify_btn.pack(side="left")
        self.merge_btn = ttk.Button(action_wrap, text="Merge", command=self.start_merge)
        self.merge_btn.pack(side="left", padx=8)

        row += 1
        self.merge_status_var = tk.StringVar(value=self.tr("ready"))
        ttk.Label(parent, textvariable=self.merge_status_var).grid(row=row, column=0, columnspan=3, sticky="w", **pad)

        row += 1
        self.merge_log = tk.Text(parent, height=20)
        self.merge_log.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        self.merge_log.insert("1.0", self.tr("choose_manifest") + "\n")
        self.merge_log.configure(state="disabled")

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

    def select_source_file(self) -> None:
        path = filedialog.askopenfilename(title=self.tr("select_source"))
        if path:
            self.source_var.set(path)

    def select_manifest_file(self) -> None:
        path = filedialog.askopenfilename(
            title=self.tr("select_manifest"),
            filetypes=[("Manifest JSON", "*.manifest.pkg.json"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.manifest_var.set(path)
            if not self.chunks_dir_var.get().strip():
                self.chunks_dir_var.set(str(Path(path).parent))

    def select_chunks_dir(self) -> None:
        path = filedialog.askdirectory(title=self.tr("select_chunk_folder"))
        if path:
            self.chunks_dir_var.set(path)

    def _append_log(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.insert("end", text + "\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _set_split_status(self, text: str) -> None:
        self.split_status_var.set(text)

    def _set_merge_status(self, text: str) -> None:
        self.merge_status_var.set(text)

    def start_split(self) -> None:
        threading.Thread(target=self._split_worker, daemon=True).start()

    def _split_worker(self) -> None:
        try:
            source_path = Path(self.source_var.get().strip())
            if not source_path.is_file():
                self._set_split_status(self.tr("invalid_source"))
                return

            size_text = self.chunk_size_var.get().strip()
            if not size_text.isdigit() or int(size_text) <= 0:
                self._set_split_status(self.tr("invalid_size"))
                return

            chunk_size = bytes_from_unit(int(size_text), self.chunk_unit_var.get())
            output_name = self.output_name_var.get().strip() or source_path.name

            custom_prefix = self.prefix_name_var.get().strip()
            base_prefix = safe_base_name(custom_prefix or source_path.name)
            prefix = random_id(10) if self.random_prefix_var.get() else base_prefix

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = source_path.parent / f"{prefix}_output_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)

            self._set_split_status(self.tr("splitting"))
            self._append_log(self.split_log, f"{self.tr('output_folder')}: {output_dir}")

            original_size = source_path.stat().st_size
            total_chunks = (original_size + chunk_size - 1) // chunk_size

            manifest = {
                "format": "splitmerge.pkg.v1",
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "originalName": source_path.name,
                "outputName": output_name,
                "originalType": "application/octet-stream",
                "originalSize": original_size,
                "chunkSizeBytes": chunk_size,
                "chunkSizeInput": {"value": int(size_text), "unit": self.chunk_unit_var.get()},
                "totalChunks": total_chunks,
                "chunks": [],
            }

            with source_path.open("rb") as src:
                for i in range(total_chunks):
                    part = src.read(chunk_size)
                    if not part:
                        break

                    if self.random_each_var.get():
                        chunk_name = f"{random_id(12)}.pkg"
                    else:
                        chunk_name = f"{prefix}.part{str(i + 1).zfill(4)}.pkg"

                    chunk_path = output_dir / chunk_name
                    with chunk_path.open("wb") as out:
                        out.write(part)

                    digest = hashlib.sha256(part).hexdigest()
                    manifest["chunks"].append(
                        {"index": i, "name": chunk_name, "size": len(part), "sha256": digest}
                    )

                    self._append_log(
                        self.split_log,
                        self.tr("split_line", idx=i + 1, total=total_chunks, name=chunk_name, size=len(part)),
                    )

            manifest_path = output_dir / f"{prefix}.manifest.pkg.json"
            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            self._append_log(self.split_log, f"{self.tr('manifest_saved')}: {manifest_path}")

            if self.release_program_var.get():
                self._release_main_program_to(output_dir)

            self._set_split_status(self.tr("split_done"))
            messagebox.showinfo(self.tr("done"), self.tr("split_completed", path=output_dir))
        except Exception as exc:
            self._set_split_status(self.tr("split_failed"))
            self._append_log(self.split_log, f"Error: {exc}")

    def _release_main_program_to(self, output_dir: Path) -> None:
        try:
            self._append_log(self.split_log, f"{self.tr('releasing_program')}...")

            if getattr(sys, "frozen", False):
                source_program = Path(sys.executable)
            else:
                source_program = Path(__file__).resolve()

            if not source_program.exists():
                self._append_log(self.split_log, f"{self.tr('release_program_failed')}: source not found")
                return

            target_program = output_dir / source_program.name
            if source_program.resolve() != target_program.resolve():
                shutil.copy2(source_program, target_program)

            self._append_log(self.split_log, f"{self.tr('release_program_done')}: {target_program}")

            if target_program.suffix.lower() == ".py":
                launcher = output_dir / "run_splitmerge_desktop.bat"
                launcher.write_text(
                    "@echo off\r\n"
                    "setlocal\r\n"
                    f'python "%~dp0{target_program.name}"\r\n',
                    encoding="utf-8",
                )
                self._append_log(self.split_log, f"{self.tr('released_bat')}: {launcher}")
        except Exception as exc:
            self._append_log(self.split_log, f"{self.tr('release_program_failed')}: {exc}")

    def _load_manifest(self):
        manifest_path = Path(self.manifest_var.get().strip())
        chunks_dir = Path(self.chunks_dir_var.get().strip())

        if not manifest_path.is_file():
            raise ValueError(self.tr("manifest_invalid"))
        if not chunks_dir.is_dir():
            raise ValueError(self.tr("chunk_folder_invalid"))

        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        return manifest_path, chunks_dir, manifest

    def start_verify(self) -> None:
        threading.Thread(target=self._verify_worker, daemon=True).start()

    def _verify_worker(self) -> None:
        try:
            self._set_merge_status(self.tr("verify_start"))
            manifest_path, chunks_dir, manifest = self._load_manifest()
            _ = manifest_path

            missing = []
            bad_hash = []
            expected_names = set()

            chunks = sorted(manifest.get("chunks", []), key=lambda x: x.get("index", 0))
            for chunk in chunks:
                name = chunk["name"]
                expected_names.add(name)
                chunk_path = chunks_dir / name
                if not chunk_path.is_file():
                    missing.append(name)
                    continue
                digest = sha256_file(chunk_path)
                if digest != chunk.get("sha256"):
                    bad_hash.append(name)

            extra = []
            for file_name in os.listdir(chunks_dir):
                if file_name.endswith(".pkg") and file_name not in expected_names:
                    extra.append(file_name)

            self._append_log(self.merge_log, f"{self.tr('expected_chunks')}: {len(chunks)}")
            self._append_log(self.merge_log, f"{self.tr('missing')}: {', '.join(missing) if missing else self.tr('none')}")
            self._append_log(self.merge_log, f"{self.tr('hash_mismatch')}: {', '.join(bad_hash) if bad_hash else self.tr('none')}")
            if extra:
                self._append_log(self.merge_log, f"{self.tr('extra_ignored')}: {', '.join(extra)}")

            if missing or bad_hash:
                self._set_merge_status(self.tr("verify_failed"))
                return

            self._set_merge_status(self.tr("verify_passed"))
        except Exception as exc:
            self._set_merge_status(self.tr("verify_error"))
            self._append_log(self.merge_log, f"Error: {exc}")

    def start_merge(self) -> None:
        threading.Thread(target=self._merge_worker, daemon=True).start()

    def _merge_worker(self) -> None:
        try:
            self._set_merge_status(self.tr("merge_start"))
            manifest_path, chunks_dir, manifest = self._load_manifest()

            chunks = sorted(manifest.get("chunks", []), key=lambda x: x.get("index", 0))
            for chunk in chunks:
                chunk_path = chunks_dir / chunk["name"]
                if not chunk_path.is_file():
                    raise ValueError(f"{self.tr('missing_chunk')}: {chunk['name']}")
                digest = sha256_file(chunk_path)
                if digest != chunk.get("sha256"):
                    raise ValueError(f"{self.tr('hash_bad')}: {chunk['name']}")

            output_name = manifest.get("outputName") or manifest.get("originalName") or "merged.bin"
            merged_path = manifest_path.parent / output_name

            with merged_path.open("wb") as out:
                for i, chunk in enumerate(chunks, start=1):
                    chunk_path = chunks_dir / chunk["name"]
                    with chunk_path.open("rb") as src:
                        out.write(src.read())
                    self._append_log(self.merge_log, self.tr("merged_line", idx=i, total=len(chunks), name=chunk["name"]))

            self._set_merge_status(self.tr("merge_done"))
            self._append_log(self.merge_log, f"{self.tr('merged_file')}: {merged_path}")
            messagebox.showinfo(self.tr("done"), self.tr("merge_completed", path=merged_path))
        except Exception as exc:
            self._set_merge_status(self.tr("merge_failed"))
            self._append_log(self.merge_log, f"Error: {exc}")


def main() -> None:
    root = tk.Tk()
    app = SplitMergeApp(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()