
import duckdb
import os

DB_PATH = '../../data/vantage.duckdb'
EXPORT_DIR = '../../data/export'

def export_to_parquet():
    print(f"Connecting to {DB_PATH}...")
    try:
        con = duckdb.connect(DB_PATH)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    # Ensure export directory exists
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Models to export (Production Marts)
    models = [
        # Marts
        'main.fct_orders',
        'main.fct_transactions',
        'main.dim_product_current',
        'main.dim_product_history',
        'main.dim_calendar',
        'main.fct_budget_daily'
    ]

    import zipfile

    print(f"Exporting models to {EXPORT_DIR}...")
    
    exported_files = []

    for model in models:
        table_name = model.split('.')[1] # e.g. fct_orders
        
        # 1. Export Parquet
        parquet_file = os.path.join(EXPORT_DIR, f"{table_name}.parquet")
        print(f"  -> Exporting {model} to {parquet_file}")
        try:
            query = f"COPY (SELECT * FROM {model}) TO '{parquet_file}' (FORMAT PARQUET)"
            con.execute(query)
            exported_files.append(f"{table_name}.parquet")
            print(f"     Success (Parquet).")
        except Exception as e:
            print(f"     FAILED (Parquet): {e}")

        # 2. Export CSV
        csv_file = os.path.join(EXPORT_DIR, f"{table_name}.csv")
        print(f"  -> Exporting {model} to {csv_file}")
        try:
            query = f"COPY (SELECT * FROM {model}) TO '{csv_file}' (FORMAT CSV, HEADER)"
            con.execute(query)
            exported_files.append(f"{table_name}.csv")
            print(f"     Success (CSV).")
        except Exception as e:
            print(f"     FAILED (CSV): {e}")

    con.close()
    
    # 3. Create Zip File
    zip_path = os.path.join(EXPORT_DIR, "bi_export.zip")
    print(f"Creating archive {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in exported_files:
                file_path = os.path.join(EXPORT_DIR, file)
                zipf.write(file_path, arcname=file)
        print("Archive created successfully.")
    except Exception as e:
        print(f"FAILED to create archive: {e}")

    print("Export Complete.")

if __name__ == "__main__":
    export_to_parquet()
