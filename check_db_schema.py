#!/usr/bin/env python3
import os
import sys
sys.path.append('src')

from sqlalchemy import create_engine, text
from api.db.config import DATABASE_URL

def check_database_schema():
    print(f"Connecting to: {DATABASE_URL}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("\n=== Checking table 'order' structure ===")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'order' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                for col in columns:
                    print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("  Table 'order' not found")
            
            print("\n=== Checking table 'orders' structure ===")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'orders' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                for col in columns:
                    print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("  Table 'orders' not found")
            
            print("\n=== Checking enum 'orderstatus' values ===")
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'orderstatus'
                )
                ORDER BY enumsortorder;
            """))
            
            enum_values = result.fetchall()
            if enum_values:
                print("  orderstatus enum values:")
                for val in enum_values:
                    print(f"    - {val[0]}")
            else:
                print("  Enum 'orderstatus' not found")
            
            print("\n=== Checking all tables ===")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            print("  Available tables:")
            for table in tables:
                print(f"    - {table[0]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database_schema() 