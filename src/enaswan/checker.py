import hashlib
import pandas as pd
import os
import sys
from tqdm import tqdm


def calculate_md5_with_progress(fname):
    """Calculates MD5 while showing a per-file progress bar."""
    hash_md5 = hashlib.md5()
    try:
        file_size = os.path.getsize(fname)
        with open(fname, "rb") as f:
            with tqdm(
                total=file_size,
                unit='B',
                unit_scale=True,
                desc=f"  ↳ Hashing {os.path.basename(fname)}",
                leave=False
            ) as pbar:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    hash_md5.update(chunk)
                    pbar.update(len(chunk))
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None


def run_check(metadata_csv):
    """Entry point for `enaswan --check`. Verifies MD5 checksums from a metadata CSV."""
    print(f"\n🛡️  ENASWAN Integrity Guard: Validating {metadata_csv}")
    print("-" * 50)

    try:
        df = pd.read_csv(metadata_csv)
    except Exception as e:
        print(f"❌ Critical Error: Could not read CSV. {e}")
        sys.exit(1)

    if 'fastq_md5' not in df.columns or 'fastq_ftp' not in df.columns:
        print("❌ Data Error: Metadata CSV is missing 'fastq_md5' or 'fastq_ftp' columns.")
        print("   Tip: Generate the metadata CSV first with: enaswan --meta <ID>")
        sys.exit(1)

    results = []

    for _, row in df.iterrows():
        expected_md5s = str(row['fastq_md5']).split(';')
        ftp_links     = str(row['fastq_ftp']).split(';')

        for i, link in enumerate(ftp_links):
            filename = os.path.basename(link)
            expected = expected_md5s[i] if i < len(expected_md5s) else None

            if not expected or expected.strip() == 'nan':
                continue

            actual = calculate_md5_with_progress(filename)

            if actual is None:
                status     = "MISSING ⚡"
                color_code = "\033[93m"   # Yellow
            elif actual.lower() == expected.lower():
                status     = "PASS ✅"
                color_code = "\033[92m"   # Green
            else:
                status     = "CORRUPTED ❌"
                color_code = "\033[91m"   # Red

            print(f"{color_code}{status}\033[0m | {filename}")
            results.append({"File": filename, "Status": status})

    if not results:
        print("⚠️  No files found to verify.")
        return

    summary = pd.DataFrame(results)
    print("\n" + "=" * 40)
    print("         FINAL INTEGRITY REPORT")
    print("=" * 40)
    for label, count in summary['Status'].value_counts().items():
        print(f"{label:20}: {count} file(s)")
    print("=" * 40)

    if "CORRUPTED ❌" in summary['Status'].values:
        print("\n🚨 ACTION REQUIRED: One or more files are corrupted. Please re-download.")
        sys.exit(1)
    else:
        print("\n🌟 All files verified successfully. Data is safe for analysis.")
