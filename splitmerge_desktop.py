import hashlib
import json
import os
import random
import string
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
        self.root.title("SplitMerge Desktop Tool")
        self.root.geometry("860x620")
        self.root.minsize(760, 520)

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        split_frame = ttk.Frame(notebook)
        merge_frame = ttk.Frame(notebook)
        notebook.add(split_frame, text="Split")
        notebook.add(merge_frame, text="Merge")

        self._build_split_tab(split_frame)
        self._build_merge_tab(merge_frame)

    def _build_split_tab(self, parent: ttk.Frame) -> None:
        pad = {"padx": 8, "pady": 6}

        self.source_var = tk.StringVar()
        self.chunk_size_var = tk.StringVar(value="10")
        self.chunk_unit_var = tk.StringVar(value="MB")
        self.output_name_var = tk.StringVar()
        self.prefix_name_var = tk.StringVar()
        self.random_prefix_var = tk.BooleanVar(value=False)
        self.random_each_var = tk.BooleanVar(value=False)

        row = 0
        ttk.Label(parent, text="Source file").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.source_var, width=80).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(parent, text="Browse", command=self.select_source_file).grid(row=row, column=2, **pad)

        row += 1
        ttk.Label(parent, text="Chunk size").grid(row=row, column=0, sticky="w", **pad)
        size_wrap = ttk.Frame(parent)
        size_wrap.grid(row=row, column=1, sticky="w", **pad)
        ttk.Entry(size_wrap, textvariable=self.chunk_size_var, width=16).pack(side="left")
        ttk.Combobox(size_wrap, textvariable=self.chunk_unit_var, values=["KB", "MB"], width=6, state="readonly").pack(side="left", padx=6)

        row += 1
        ttk.Label(parent, text="Merged output filename (optional)").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.output_name_var, width=80).grid(row=row, column=1, columnspan=2, sticky="ew", **pad)

        row += 1
        ttk.Label(parent, text="Chunk filename prefix (optional)").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.prefix_name_var, width=80).grid(row=row, column=1, columnspan=2, sticky="ew", **pad)

        row += 1
        checks_wrap = ttk.Frame(parent)
        checks_wrap.grid(row=row, column=1, columnspan=2, sticky="w", **pad)
        ttk.Checkbutton(checks_wrap, text="Use random chunk prefix", variable=self.random_prefix_var).pack(anchor="w")
        ttk.Checkbutton(checks_wrap, text="Use random name for each chunk", variable=self.random_each_var).pack(anchor="w")

        row += 1
        action_wrap = ttk.Frame(parent)
        action_wrap.grid(row=row, column=1, columnspan=2, sticky="w", **pad)
        ttk.Button(action_wrap, text="Start Split", command=self.start_split).pack(side="left")

        row += 1
        self.split_status_var = tk.StringVar(value="Ready.")
        ttk.Label(parent, textvariable=self.split_status_var).grid(row=row, column=0, columnspan=3, sticky="w", **pad)

        row += 1
        self.split_log = tk.Text(parent, height=18)
        self.split_log.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        self.split_log.insert("1.0", "Waiting for input.\n")
        self.split_log.configure(state="disabled")

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

    def _build_merge_tab(self, parent: ttk.Frame) -> None:
        pad = {"padx": 8, "pady": 6}

        self.manifest_var = tk.StringVar()
        self.chunks_dir_var = tk.StringVar()

        row = 0
        ttk.Label(parent, text="Manifest file (.manifest.pkg.json)").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.manifest_var, width=80).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(parent, text="Browse", command=self.select_manifest_file).grid(row=row, column=2, **pad)

        row += 1
        ttk.Label(parent, text="Chunk folder").grid(row=row, column=0, sticky="w", **pad)
        ttk.Entry(parent, textvariable=self.chunks_dir_var, width=80).grid(row=row, column=1, sticky="ew", **pad)
        ttk.Button(parent, text="Browse", command=self.select_chunks_dir).grid(row=row, column=2, **pad)

        row += 1
        action_wrap = ttk.Frame(parent)
        action_wrap.grid(row=row, column=1, columnspan=2, sticky="w", **pad)
        ttk.Button(action_wrap, text="Verify", command=self.start_verify).pack(side="left")
        ttk.Button(action_wrap, text="Merge", command=self.start_merge, style="Accent.TButton").pack(side="left", padx=8)

        row += 1
        self.merge_status_var = tk.StringVar(value="Ready.")
        ttk.Label(parent, textvariable=self.merge_status_var).grid(row=row, column=0, columnspan=3, sticky="w", **pad)

        row += 1
        self.merge_log = tk.Text(parent, height=20)
        self.merge_log.grid(row=row, column=0, columnspan=3, sticky="nsew", **pad)
        self.merge_log.insert("1.0", "Choose manifest and chunk folder.\n")
        self.merge_log.configure(state="disabled")

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

    def select_source_file(self) -> None:
        path = filedialog.askopenfilename(title="Select source file")
        if path:
            self.source_var.set(path)

    def select_manifest_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select manifest file",
            filetypes=[("Manifest JSON", "*.manifest.pkg.json"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.manifest_var.set(path)
            if not self.chunks_dir_var.get().strip():
                self.chunks_dir_var.set(str(Path(path).parent))

    def select_chunks_dir(self) -> None:
        path = filedialog.askdirectory(title="Select chunk folder")
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
                self._set_split_status("Please select a valid source file.")
                return

            size_text = self.chunk_size_var.get().strip()
            if not size_text.isdigit() or int(size_text) <= 0:
                self._set_split_status("Chunk size must be a positive integer.")
                return

            chunk_size = bytes_from_unit(int(size_text), self.chunk_unit_var.get())
            output_name = self.output_name_var.get().strip() or source_path.name

            custom_prefix = self.prefix_name_var.get().strip()
            base_prefix = safe_base_name(custom_prefix or source_path.name)
            prefix = random_id(10) if self.random_prefix_var.get() else base_prefix

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = source_path.parent / f"{prefix}_output_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)

            self._set_split_status("Splitting...")
            self._append_log(self.split_log, f"Output folder: {output_dir}")

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
                        f"[{i + 1}/{total_chunks}] {chunk_name} ({len(part)} bytes)",
                    )

            manifest_path = output_dir / f"{prefix}.manifest.pkg.json"
            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            self._append_log(self.split_log, f"Manifest: {manifest_path}")
            self._set_split_status("Split done.")
            messagebox.showinfo("Done", f"Split completed.\nOutput folder:\n{output_dir}")
        except Exception as exc:
            self._set_split_status("Split failed.")
            self._append_log(self.split_log, f"Error: {exc}")

    def _load_manifest(self):
        manifest_path = Path(self.manifest_var.get().strip())
        chunks_dir = Path(self.chunks_dir_var.get().strip())

        if not manifest_path.is_file():
            raise ValueError("Manifest file is invalid.")
        if not chunks_dir.is_dir():
            raise ValueError("Chunk folder is invalid.")

        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        return manifest_path, chunks_dir, manifest

    def start_verify(self) -> None:
        threading.Thread(target=self._verify_worker, daemon=True).start()

    def _verify_worker(self) -> None:
        try:
            self._set_merge_status("Verifying...")
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

            self._append_log(self.merge_log, f"Expected chunks: {len(chunks)}")
            self._append_log(self.merge_log, f"Missing: {', '.join(missing) if missing else 'None'}")
            self._append_log(self.merge_log, f"Hash mismatch: {', '.join(bad_hash) if bad_hash else 'None'}")
            if extra:
                self._append_log(self.merge_log, f"Extra pkg files (ignored): {', '.join(extra)}")

            if missing or bad_hash:
                self._set_merge_status("Verification failed.")
                return

            self._set_merge_status("Verification passed.")
        except Exception as exc:
            self._set_merge_status("Verify failed.")
            self._append_log(self.merge_log, f"Error: {exc}")

    def start_merge(self) -> None:
        threading.Thread(target=self._merge_worker, daemon=True).start()

    def _merge_worker(self) -> None:
        try:
            self._set_merge_status("Merging...")
            manifest_path, chunks_dir, manifest = self._load_manifest()

            chunks = sorted(manifest.get("chunks", []), key=lambda x: x.get("index", 0))
            for chunk in chunks:
                chunk_path = chunks_dir / chunk["name"]
                if not chunk_path.is_file():
                    raise ValueError(f"Missing chunk: {chunk['name']}")
                digest = sha256_file(chunk_path)
                if digest != chunk.get("sha256"):
                    raise ValueError(f"Hash mismatch: {chunk['name']}")

            output_name = manifest.get("outputName") or manifest.get("originalName") or "merged.bin"
            merged_path = manifest_path.parent / output_name

            with merged_path.open("wb") as out:
                for i, chunk in enumerate(chunks, start=1):
                    chunk_path = chunks_dir / chunk["name"]
                    with chunk_path.open("rb") as src:
                        out.write(src.read())
                    self._append_log(self.merge_log, f"[{i}/{len(chunks)}] merged {chunk['name']}")

            self._set_merge_status("Merge done.")
            self._append_log(self.merge_log, f"Merged file: {merged_path}")
            messagebox.showinfo("Done", f"Merge completed.\nOutput file:\n{merged_path}")
        except Exception as exc:
            self._set_merge_status("Merge failed.")
            self._append_log(self.merge_log, f"Error: {exc}")


def main() -> None:
    root = tk.Tk()
    app = SplitMergeApp(root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()