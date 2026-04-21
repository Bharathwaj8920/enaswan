# 🦢 enaswan

**ENA Smart Workflow and Acquisition Network**

A fast, parallel command-line toolkit to fetch metadata, download FASTQ files, and verify integrity from the [European Nucleotide Archive (ENA)](https://www.ebi.ac.uk/ena).

\---

## Installation

### Via pip (PyPI)

```bash
pip install enaswan
```

### Via conda (Bioconda)

```bash
conda install -c bioconda enaswan
```

\---

## Workflow

Run the three steps in order:

### Step 1 — Fetch Metadata

```bash
enaswan --meta SRR12345678
enaswan --meta SRR12345678 ERR000001 PRJNA123456   # multiple IDs
enaswan --meta SRR12345678 --outdir ./results       # custom output folder
```

Saves a `<ID>\_metadata.csv` file containing run accession, sample info,
instrument model, file sizes, FTP links, and MD5 checksums.

\---

### Step 2 — Download FASTQ Files

```bash
enaswan --dl SRR12345678
enaswan --dl SRR12345678 ERR000001                  # multiple IDs
enaswan --dl SRR12345678 --threads 8 --outdir ./data  # parallel + custom dir
```

* Downloads are **parallel** (default: 4 threads)
* **Resumes** interrupted downloads automatically
* Shows a real-time progress bar

> 📶 Note: Download speed will vary depending on the internet connection and ENA server load.

\---

### Step 3 — Verify Integrity

```bash
enaswan --check SRR12345678_metadata.csv
```

Computes MD5 checksums for each downloaded file and compares against
ENA's expected values. Reports PASS ✅, MISSING ⚡, or CORRUPTED ❌.

\---

## Full Options

```
usage: enaswan \[-h] (--meta ID \[ID ...] | --dl ID \[ID ...] | --check metadata.csv)
               \[--threads N] \[--outdir DIR]

options:
  --meta   ID \[ID ...]    Fetch metadata CSV for accession IDs
  --dl     ID \[ID ...]    Download FASTQ files for accession IDs
  --check  metadata.csv   Verify MD5 checksums using metadata CSV
  --threads N             Parallel download threads (default: 4)
  --outdir DIR            Output directory (default: current directory)
```

\---

## Supported Accession Types

|Type|Example|Description|
|-|-|-|
|Run|SRR\*, ERR\*, DRR\*|Single sequencing run|
|Project|PRJNA\*, PRJEB\*|All runs in a project|
|Sample|SAMN\*, SAME\*|All runs for a sample|

\---

## License

MIT © Bandari Bharathwaj


# enaswan
ENA Smart Workflow and Acquisition Network — fast parallel FASTQ downloader for the European Nucleotide Archive