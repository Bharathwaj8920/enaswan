import requests
import pandas as pd
import os


def fetch_ena_metadata(accession):
    """Queries ENA with flexible result types to avoid 400 errors."""
    api_url = "https://www.ebi.ac.uk/ena/portal/api/filereport"

    fields = (
        "study_accession,sample_accession,secondary_sample_accession,"
        "sample_alias,run_accession,scientific_name,instrument_model,"
        "library_layout,fastq_ftp,fastq_bytes,fastq_md5"
    )

    params = {
        'accession': accession,
        'result': 'read_run',
        'fields': fields,
        'format': 'json'
    }

    try:
        response = requests.get(api_url, params=params, timeout=30)

        if response.status_code == 400:
            print("🔄 Retrying with alternative API parameters...")
            params['result'] = 'analysis_run'
            response = requests.get(api_url, params=params, timeout=30)

        response.raise_for_status()

        data = response.json()
        if not data:
            return None

        df = pd.DataFrame(data)

        if 'fastq_bytes' in df.columns:
            df['size_gb'] = df['fastq_bytes'].apply(
                lambda x: round(
                    sum(int(s) for s in str(x).split(';') if s.strip()) / (1024 ** 3), 2
                )
            )

        return df

    except Exception as e:
        print(f"❌ API Error: {e}")
        return None


def run_meta(accession_list, outdir="."):
    """Entry point for `enaswan --meta`. Saves one CSV per accession."""
    os.makedirs(outdir, exist_ok=True)

    for acc in accession_list:
        print(f"\n🔍 Fetching metadata for {acc}...")
        df = fetch_ena_metadata(acc)

        if df is not None:
            output_file = os.path.join(outdir, f"{acc}_metadata.csv")
            df.to_csv(output_file, index=False)
            print(f"✅ Metadata saved to: {output_file}")
            print(f"   Rows: {len(df)} | Columns: {list(df.columns)}")
        else:
            print(f"❌ Could not retrieve metadata for {acc}. Verify the ID is public.")
