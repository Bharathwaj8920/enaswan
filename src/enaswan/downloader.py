import requests
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import (
    ConnectionError, Timeout, HTTPError,
    ChunkedEncodingError, RequestException
)


def make_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retry))
    return session


def download_one_file(args):
    url, filename, update_bar = args
    if not url.startswith('http'):
        url = 'https://' + url
    if os.path.exists(filename):
        return f"⏭️  Skipped (already exists): {filename}"

    tmp = filename + ".tmp"
    session = make_session()

    resume_from = os.path.getsize(tmp) if os.path.exists(tmp) else 0

    try:
        headers = {}
        if resume_from > 0:
            headers['Range'] = f'bytes={resume_from}-'

        r = session.get(url, stream=True, timeout=60, headers=headers)

        if resume_from > 0 and r.status_code == 200:
            resume_from = 0
            tqdm.write(
                f"⚠️  Server does not support resume for {os.path.basename(filename)}, restarting.",
                file=sys.stderr
            )

        r.raise_for_status()

        if resume_from > 0:
            update_bar(resume_from)
            tqdm.write(
                f"🔁 Resuming {os.path.basename(filename)} from {resume_from / (1024**2):.1f} MB",
                file=sys.stderr
            )

        open_mode = 'ab' if resume_from > 0 else 'wb'
        with open(tmp, open_mode) as f:
            for chunk in r.iter_content(chunk_size=256 * 1024):
                if chunk:
                    f.write(chunk)
                    update_bar(len(chunk))

        os.rename(tmp, filename)
        return f"✅ Done: {filename}"

    except ConnectionError as e:
        msg = f"❌ Network Error [{filename}]: Could not connect to ENA server. Check your internet connection.\n   Detail: {e}"
    except Timeout as e:
        msg = f"⏱️  Timeout Error [{filename}]: Server did not respond within 60s. ENA may be slow — try again later.\n   Detail: {e}"
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        msg = f"🌐 HTTP Error [{filename}]: Server returned status {status}.\n   Detail: {e}"
    except ChunkedEncodingError as e:
        msg = f"📡 Transfer Interrupted [{filename}]: Connection dropped mid-download. Re-run to resume.\n   Detail: {e}"
    except RequestException as e:
        msg = f"⚠️  Request Failed [{filename}]: Unexpected network issue.\n   Detail: {e}"
    except OSError as e:
        msg = f"💾 File System Error [{filename}]: Could not write file to disk.\n   Detail: {e}"
    except Exception as e:
        msg = f"🔥 Unexpected Error [{filename}]: {type(e).__name__}: {e}"

    return msg


def fetch_download_metadata(acc, api_url):
    """Fetch only the fields needed for downloading (ftp links + sizes)."""
    params = {
        'accession': acc,
        'result': 'read_run',
        'fields': 'run_accession,fastq_ftp,fastq_bytes',
        'format': 'json'
    }
    try:
        res = requests.get(api_url, params=params, timeout=30)
        res.raise_for_status()
        if not res.text.strip():
            print(f"  ⚠️  No data returned for accession: {acc}")
            return []
        return res.json()

    except ConnectionError as e:
        print(f"  ❌ Network Error [{acc}]: Cannot reach ENA API. Check your internet.\n     Detail: {e}")
    except Timeout as e:
        print(f"  ⏱️  Timeout [{acc}]: ENA API did not respond in 30s.\n     Detail: {e}")
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 400:
            print(f"  🔴 Bad Request [{acc}]: Accession ID may be invalid or malformed.")
        elif status == 404:
            print(f"  🔴 Not Found [{acc}]: Accession does not exist in ENA.")
        elif status == 429:
            print(f"  🔴 Rate Limited [{acc}]: Too many requests. Wait and retry.")
        elif status == 500:
            print(f"  🔴 ENA Server Error [{acc}]: Internal server error on ENA's side.")
        else:
            print(f"  🌐 HTTP Error [{acc}]: Status {status}.\n     Detail: {e}")
    except RequestException as e:
        print(f"  ⚠️  Request Failed [{acc}]: Unexpected error contacting ENA API.\n     Detail: {e}")
    return []


def run_download(accession_list, max_workers=4, outdir="."):
    """Entry point for `enaswan --dl`. Downloads FASTQ files for given accessions."""
    os.makedirs(outdir, exist_ok=True)

    all_links   = []
    total_bytes = 0
    api_url     = "https://www.ebi.ac.uk/ena/portal/api/filereport"

    print(f"\n🔍 Fetching download links for {len(accession_list)} accession(s)...")
    for acc in accession_list:
        entries = fetch_download_metadata(acc, api_url)
        for entry in entries:
            run_id = entry.get('run_accession', acc)
            links  = [l for l in entry.get('fastq_ftp', '').split(';') if l.strip()]
            if not links:
                print(f"  ⚠️  No FTP links found for {run_id}")
                continue
            sizes = [int(s) for s in str(entry.get('fastq_bytes', '0')).split(';') if s.strip()]
            total_bytes += sum(sizes)
            for link in links:
                fname = os.path.join(outdir, os.path.basename(link))
                all_links.append((link, fname))
                print(f"  📦 Queued: {os.path.basename(fname)}")

    if not all_links:
        print("\n❌ No files to download.")
        return

    print(f"\n⬇️  Downloading {len(all_links)} file(s) with {max_workers} threads...")
    print(f"📶 Note: Download speed will vary depending on your internet connection and ENA server load.\n")

    bar_lock = threading.Lock()

    with tqdm(
        total=total_bytes,
        unit='iB',
        unit_scale=True,
        desc="Total Progress",
        dynamic_ncols=True,
        file=sys.stderr
    ) as bar:
        def update_bar(n):
            with bar_lock:
                bar.update(n)

        args = [(link, fname, update_bar) for link, fname in all_links]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for result in executor.map(download_one_file, args):
                tqdm.write(result, file=sys.stderr)

    print("\n--- ✅ All downloads complete ---")
