import sqlite3
import csv
import os

def export_db_to_csv(database_name):
    """
    Exports each table from a SQLite database to its own CSV file.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()

        # Query to get all table names in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Iterate over each table
        for table_name in tables:
            table_name = table_name[0]
            csv_filename = f"{table_name}.csv"

            print(f"Exporting table '{table_name}' to '{csv_filename}'...")

            # Select all data from the current table
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            if not rows:
                print(f"Table '{table_name}' is empty. Skipping CSV creation.")
                continue

            # Get the column headers
            headers = [description[0] for description in cursor.description]

            # Create and write to the CSV file
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(rows)

        print("Export complete.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except IOError as e:
        print(f"File I/O error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_file = "econsultation.db"

    # Check if the database file exists before trying to export
    if os.path.exists(db_file):
        export_db_to_csv(db_file)
    else:
        print(f"Error: Database file '{db_file}' not found.")
        print("Please ensure the database file is in the same directory as this script.")
