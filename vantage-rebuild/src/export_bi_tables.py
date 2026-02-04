import duckdb
import os
import zipfile
import glob

def export_tables():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'data', 'vantage.duckdb')
    export_dir = os.path.join(base_dir, 'data', 'export')

    # Create export directory if it doesn't exist
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        print(f"Created export directory: {export_dir}")

    # Connect to database
    print(f"Connecting to database at: {db_path}")
    con = duckdb.connect(db_path)

    # Tables to export
    tables = [
        'dim_calendar',
        'dim_products',
        'fct_budget_daily',
        'fct_transactions'
    ]
    
    # 2. Export KPI Validation Query
    kpi_sql_path = os.path.join(base_dir, 'analysis', 'kpi_validation.sql')
    if os.path.exists(kpi_sql_path):
        print(f"Found KPI Validation SQL at: {kpi_sql_path}")
        try: 
            with open(kpi_sql_path, 'r') as f:
                kpi_query = f.read()
            
            output_file = os.path.join(export_dir, "kpi_validation.parquet")
            print(f"Exporting KPI Validation to {output_file}...")
            # Use subquery for COPY
            con.execute(f"COPY ({kpi_query}) TO '{output_file}' (FORMAT 'parquet')")
            print("Successfully exported KPI Validation (Parquet)")

            output_file_csv = os.path.join(export_dir, "kpi_validation.csv")
            print(f"Exporting KPI Validation to {output_file_csv}...")
            con.execute(f"COPY ({kpi_query}) TO '{output_file_csv}' (HEADER, DELIMITER ',')")
            print("Successfully exported KPI Validation (CSV)")
            
        except Exception as e:
            print(f"Error exporting KPI Validation: {e}")
    else:
        print(f"Warning: KPI Validation SQL not found at {kpi_sql_path}")

    try:
        for table in tables:
            output_file = os.path.join(export_dir, f"{table}.parquet")
            print(f"Exporting {table} to {output_file}...")
            
            # Check if table exists first (handling potential schema/naming differences)
            # DBT usually creates tables in the main schema or a configured schema.
            # We'll try to select from it directly.
            try:
                con.execute(f"COPY (SELECT * FROM {table}) TO '{output_file}' (FORMAT 'parquet')")
                print(f"Successfully exported {table} (Parquet)")

                # Export CSV
                output_file_csv = os.path.join(export_dir, f"{table}.csv")
                print(f"Exporting {table} to {output_file_csv}...")
                con.execute(f"COPY (SELECT * FROM {table}) TO '{output_file_csv}' (HEADER, DELIMITER ',')")
                print(f"Successfully exported {table} (CSV)")
            except duckdb.CatalogException:
                print(f"Table {table} not found. Checking available tables...")
                # List tables to help debugging if one is missing
                available_tables = con.execute("SHOW TABLES").fetchall()
                print(f"Available tables: {[t[0] for t in available_tables]}")
            except Exception as e:
                 print(f"Error exporting {table}: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close DB connection first
        try:
            con.close()
        except:
            pass
        
    # Compression happens after DB work is done
    print("Export process completed. Compressing files...")
    try:
        zip_filename = os.path.join(export_dir, 'bi_export.zip')
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Compress both Parquet and CSV files
            for file_path in glob.glob(os.path.join(export_dir, '*.parquet')) + glob.glob(os.path.join(export_dir, '*.csv')):
                arcname = os.path.basename(file_path)
                print(f"Adding {arcname} to archive...")
                zipf.write(file_path, arcname)
                
        print(f"Successfully created archive: {zip_filename}")
    except Exception as e:
        print(f"Error zipping files: {e}")
        
    print("Export script finished.")

if __name__ == "__main__":
    export_tables()
