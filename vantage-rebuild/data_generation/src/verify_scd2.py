
import duckdb
import pandas as pd

DB_PATH = '../../data/vantage.duckdb'

def run_tests():
    print(f"Connecting to {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    # helper
    def check(name, query, expected_rows=None, assert_func=None):
        print(f"\n--- Checking: {name} ---")
        try:
            df = con.execute(query).df()
            print(f"Result rows: {len(df)}")
            if len(df) > 0:
                print(df.head())
            
            if expected_rows is not None:
                if len(df) == expected_rows:
                    print(f"PASS: Row count matches expected ({expected_rows})")
                else:
                    print(f"FAIL: Row count {len(df)} != expected {expected_rows}")
            
            if assert_func:
                if assert_func(df):
                    print("PASS: Custom assertion")
                else:
                    print("FAIL: Custom assertion")
        except Exception as e:
            print(f"ERROR: {e}")

    # Inspect Schema/Types
    print("\n--- Schema Inspection ---")
    print(con.execute("DESCRIBE snapshots.snap_product").df())
    print(con.execute("DESCRIBE stg_orders").df())
    print(con.execute("DESCRIBE stg_line_items").df())
    
    # Check sample data for 10002
    print("\n--- Sample Data Inspection (Product 10002) ---")
    print(con.execute("SELECT * FROM snapshots.snap_product WHERE product_id = 10002").df())
    
    # Check date types specifically
    print("\n--- Date Type Check ---")
    # check valid_from type
    # q_type = "SELECT typeof(dbt_valid_from) FROM snap_product LIMIT 1"
    # print(con.execute(q_type).df())

    # 4.1 Snapshot Integrity
    q41 = """
    SELECT product_id, COUNT(*) AS versions
    FROM snapshots.snap_product
    GROUP BY product_id
    HAVING COUNT(*) > 2
    """
    check("4.1 Snapshot Integrity (Products with > 2 versions)", q41, expected_rows=0)

    # 4.2 No Gaps or Overlaps
    q42 = """
    SELECT
        a.product_id,
        a.dbt_valid_to AS v1_end,
        b.dbt_valid_from AS v2_start
    FROM snapshots.snap_product a
    JOIN snapshots.snap_product b
        ON a.product_id = b.product_id
        AND a.dbt_valid_to IS NOT NULL
        AND b.dbt_valid_to IS NULL
    WHERE a.dbt_valid_to != b.dbt_valid_from
    """
    check("4.2 No Gaps/Overlaps", q42, expected_rows=0)

    # 4.3 Fact Table Join Correctness
    # Need to check fct_orders. But fct_orders is a dbt model, so it might not be in duckdb file 
    # unless dbt materialized it there as table/view.
    # dbt-duckdb usually creates views or tables in the duckdb file.
    # Let's verify fct_orders exists.
    
    q43 = """
    SELECT
        f.order_date,
        f.product_id,
        f.price_tier,
        f.marketing_cost_per_order
    FROM fct_orders f
    WHERE f.product_id IN (
        SELECT product_id FROM snapshots.snap_product
        GROUP BY product_id HAVING COUNT(*) > 1
    )
    ORDER BY f.product_id, f.order_date
    LIMIT 10
    """
    check("4.3 Fact Table Join Preview", q43)

    # 4.4 Marketing Cost Consistency
    q44 = """
    SELECT *
    FROM fct_orders
    WHERE (price_tier = 'budget' AND marketing_cost_per_order != 3.0)
       OR (price_tier = 'mid' AND marketing_cost_per_order != 7.0)
       OR (price_tier = 'premium' AND marketing_cost_per_order != 12.0)
    """
    check("4.4 Marketing Cost Consistency", q44, expected_rows=0)

    con.close()

if __name__ == "__main__":
    run_tests()
