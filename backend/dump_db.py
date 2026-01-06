
import sqlite3

def dump_to_sql(db_name="kioskai.db", output_file="local_backup.sql"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            # Skip internal sqlite tables
            if table.startswith('sqlite_'):
                continue
                
            # Get table schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
            schema = cursor.fetchone()[0]
            f.write(f"{schema};\n\n")
            
            # Get data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Get column names for cleaner inserts (optional, but good practice)
            # cursor.execute(f"PRAGMA table_info({table})")
            # columns = [col[1] for col in cursor.fetchall()]
            # col_str = ",".join(columns)

            for row in rows:
                # Format values
                values = []
                for val in row:
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        # Escape single quotes
                        escaped_val = str(val).replace("'", "''")
                        values.append(f"'{escaped_val}'")
                
                val_str = ", ".join(values)
                f.write(f"INSERT INTO {table} VALUES ({val_str});\n")
            
            f.write("\n")
            
    conn.close()
    print(f"Dumped database to {output_file}")

if __name__ == "__main__":
    dump_to_sql()
