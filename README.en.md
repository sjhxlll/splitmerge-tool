# splitmerge-tool

[中文](README.md)

A browser-based file split/merge tool that splits large files into `.pkg` chunks and automatically generates a standalone HTML merger page for one-click integrity check and merge download.

## Features

- Split output in `.pkg` format
- Split size supports `KB` / `MB`
- Pure `HTML + JavaScript`, no backend required
- Automatically generates a standalone merger page (`.merge.html`)
- One-click integrity checks:
  - whether any chunk is missing
  - which chunks are missing
  - whether chunk hashes match
- Supports custom merged output filename
- Supports random chunk prefix and per-chunk random filenames
- Download modes:
  - Batch download (single ZIP)
  - Single one-by-one download (to reduce popup annoyance)
- UI defaults to Chinese with one-click Chinese/English switch
- Generated merger page also supports Chinese/English switch

## Project Structure

- `index.html`: Main tool page (split + merger generator)
- `splitmerge_desktop.py`: Desktop app (no browser dependency)
- `build_exe.bat`: One-click Windows build script (creates exe)

## Desktop (EXE) Usage

If you do not want to rely on a browser, use the desktop app:

1. Install Python 3.10+ (and add it to PATH).
2. Run: `build_exe.bat`
3. After build, launch `dist/splitmerge-desktop.exe`.

Desktop capabilities:

- Split tab:
  - Splits into `.pkg` chunks
  - Automatically creates an output folder in source file directory: `<prefix>_output_<timestamp>`
  - Writes `*.manifest.pkg.json`
- Merge tab:
  - Loads manifest
  - Verifies missing chunks and hashes
  - Merges into original output filename (or custom name)

## Quick Start

1. Clone or download this repository.
2. Open `index.html` directly in your browser.
3. Select a source file to split.
4. Configure split size (KB/MB), output filename, and chunk naming mode.
5. Click "Split & Generate".
6. Choose a download mode:
   - Batch ZIP download
   - Single download list

## Generated Files

After splitting, the tool generates:

- `*.part0001.pkg`, `*.part0002.pkg`, ... (or random `.pkg` names)
- `*.manifest.pkg.json`: chunk manifest and hashes
- `*.merge.html`: standalone merger page

## Chunk Naming Options

- Use random chunk prefix:
  - Replaces the chunk prefix with a random string (for example, `a8k2m1x9qz`).
  - In ordered naming mode, chunks become names like `a8k2m1x9qz.part0001.pkg`.
  - Also affects generated file names such as `a8k2m1x9qz.manifest.pkg.json` and `a8k2m1x9qz.merge.html`.
- Use random filename for each chunk:
  - Each `.pkg` chunk gets its own independent random name (for example, `k3f8p2m1t0ab.pkg`, `q1z7c9n4r2de.pkg`).
  - No longer uses continuous `prefix.part0001.pkg` style naming.
  - Manual sorting is not needed during merge. The generated manifest stores mapping info, and the merger validates and reorders chunks automatically.

## Merge Workflow

1. Open the generated `*.merge.html`.
2. Select all `.pkg` chunk files.
3. Click "Detect completeness".
4. If integrity passes, click "Merge & Download" to rebuild the original file (or renamed target file).

## Browser Compatibility

Use latest Chrome / Edge / Firefox with support for:

- `File API`
- `Blob`
- `Web Crypto API` (SHA-256)

## Notes

- Batch ZIP export depends on CDN-hosted `JSZip`. If unavailable, the tool falls back to single-download-list mode automatically.
- If downloads are blocked by browser policy, allow downloads for the site or use one-by-one mode.
- For very large files, browser memory limits may apply. Consider using smaller chunk size.

## License

No LICENSE file is currently included in this repository. Add one if needed (for example, MIT).
