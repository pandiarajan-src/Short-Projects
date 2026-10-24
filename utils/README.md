# utils

A small collection of helper scripts I keep around.

## download_url_files.py

Recursively downloads files and subfolders from a given URL into a local directory.

```bash
python download_url_files.py
```

The module exposes `download_files(url, save_dir)` which walks the links on the page and saves every file and subfolder under `save_dir`. Requires `requests` and `beautifulsoup4`.