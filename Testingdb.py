import sqlite3

# Path to your SQLite database
db_path = 'econsultation.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the list of all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if not tables:
    print("No tables found in the database.")
else:
    print(f"Tables found in {db_path}:\n")
    for table_name in tables:
        table = table_name[0]
        print(f"--- Table: {table} ---")

        # Get the table schema
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()

        if columns:
            print("Columns:")
            for col in columns:
                cid, name, dtype, notnull, dflt_value, pk = col
                print(f"  - {name} ({dtype}), Not Null: {bool(notnull)}, Default: {dflt_value}, Primary Key: {bool(pk)}")
        else:
            print("No column info available.")
        print()

# Close the connection
conn.close()
