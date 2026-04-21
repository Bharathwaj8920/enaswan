"""
enaswan — ENA download toolkit
Usage:
  enaswan --meta  <ID> [ID ...]          Fetch metadata CSV
  enaswan --dl    <ID> [ID ...]          Download FASTQ files
  enaswan --check <metadata.csv>         Verify MD5 checksums
"""

import argparse
import sys


BANNER = r"""
  ___ _ __   __ _ _____      ____ _ _ __
 / _ \ '_ \ / _` / __\ \ /\ / / _` | '_ \\
|  __/ | | | (_| \__ \\ V  V / (_| | | | |
 \___|_| |_|\__,_|___/ \_/\_/ \__,_|_| |_|

 ENA Smart Workflow and Acquisition Network
"""


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        prog="enaswan",
        description="ENA Smart Workflow and Acquisition Network — fetch, download, and verify ENA data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow (run in this order):
  Step 1 — Fetch metadata:   enaswan --meta  SRR12345678
  Step 2 — Download files:   enaswan --dl    SRR12345678
  Step 3 — Verify integrity: enaswan --check SRR12345678_metadata.csv

Multiple IDs:
  enaswan --meta  SRR12345678 ERR000001 PRJNA123456
  enaswan --dl    SRR12345678 ERR000001 --threads 8 --outdir ./data
        """
    )

    # Mutually exclusive: only one mode per run
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        '--meta',
        nargs='+',
        metavar='ID',
        help="Fetch metadata for one or more ENA/SRA accession IDs and save as CSV"
    )
    mode.add_argument(
        '--dl',
        nargs='+',
        metavar='ID',
        help="Download FASTQ files for one or more ENA/SRA accession IDs"
    )
    mode.add_argument(
        '--check',
        metavar='metadata.csv',
        help="Verify MD5 checksums of downloaded files using a metadata CSV"
    )

    # Optional flags (apply to --dl)
    parser.add_argument(
        '--threads',
        type=int,
        default=4,
        metavar='N',
        help="Number of parallel download threads (default: 4, used with --dl)"
    )
    parser.add_argument(
        '--outdir',
        default='.',
        metavar='DIR',
        help="Output directory for downloads or metadata CSVs (default: current directory)"
    )

    # Print help if no arguments given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # ── Route to the correct module ──────────────────────────────────────────

    if args.meta:
        from enaswan.metadata import run_meta
        run_meta(args.meta, outdir=args.outdir)

    elif args.dl:
        from enaswan.downloader import run_download
        run_download(args.dl, max_workers=args.threads, outdir=args.outdir)

    elif args.check:
        from enaswan.checker import run_check
        run_check(args.check)


if __name__ == "__main__":
    main()
