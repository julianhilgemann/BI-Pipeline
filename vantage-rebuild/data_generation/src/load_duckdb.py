
import duckdb
import os


DB_PATH = '../../data/vantage.duckdb'
CSV_DIR = '../output'


def load_data():
    print(f"Connecting to {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    files = {
        'raw_orders': 'raw_orders.csv',
        'raw_line_items': 'raw_line_items.csv',
        'raw_products': 'raw_products.csv',
        'raw_marketing_daily': 'raw_marketing_daily.csv',
        'raw_budget': 'raw_budget.csv',
        'snap_product': 'raw_product_snapshots.csv'
    }
    
    for table_name, csv_file in files.items():
        csv_path = os.path.join(CSV_DIR, csv_file)
        if os.path.exists(csv_path):
            print(f"Loading {table_name} from {csv_path}...")
            # Drop and Reload pattern
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')")
            
            # Special handling for snap_product: Move to snapshots schema
            if table_name == 'snap_product':
                con.execute("CREATE SCHEMA IF NOT EXISTS snapshots")
                con.execute("DROP TABLE IF EXISTS snapshots.snap_product")
                con.execute("CREATE TABLE snapshots.snap_product AS SELECT * FROM snap_product")
                # Drop main table to avoid confusion
                con.execute("DROP TABLE snap_product")
                print("Moved snap_product to snapshots schema.")
        else:
            print(f"WARNING: {csv_path} not found!")

    # Verify
    print("\nTable Counts:")
    for table in files.keys():
        try:
            count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"- {table}: {count}")
        except:
            print(f"- {table}: ERROR")

    con.close()
    print("Database Load Complete.")

if __name__ == "__main__":
    load_data()
