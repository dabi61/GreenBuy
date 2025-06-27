from fastapi import APIRouter
from sqlalchemy import text
from api.db.session import engine

router = APIRouter()

@router.get("/schema-check")
def check_database_schema():
    """Debug endpoint để kiểm tra database schema"""
    result = {
        "order_table": [],
        "orders_table": [],
        "orderstatus_enum": [],
        "all_tables": [],
        "error": None
    }
    
    try:
        with engine.connect() as conn:
            # Check table 'order' structure
            try:
                query_result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'order' 
                    ORDER BY ordinal_position;
                """))
                result["order_table"] = [
                    {"name": row[0], "type": row[1], "nullable": row[2] == "YES"}
                    for row in query_result.fetchall()
                ]
            except Exception as e:
                result["order_table"] = [f"Error: {str(e)}"]
            
            # Check table 'orders' structure  
            try:
                query_result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'orders' 
                    ORDER BY ordinal_position;
                """))
                result["orders_table"] = [
                    {"name": row[0], "type": row[1], "nullable": row[2] == "YES"}
                    for row in query_result.fetchall()
                ]
            except Exception as e:
                result["orders_table"] = [f"Error: {str(e)}"]
            
            # Check enum 'orderstatus' values
            try:
                query_result = conn.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum 
                    WHERE enumtypid = (
                        SELECT oid FROM pg_type WHERE typname = 'orderstatus'
                    )
                    ORDER BY enumsortorder;
                """))
                result["orderstatus_enum"] = [row[0] for row in query_result.fetchall()]
            except Exception as e:
                result["orderstatus_enum"] = [f"Error: {str(e)}"]
            
            # Check all tables
            try:
                query_result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """))
                result["all_tables"] = [row[0] for row in query_result.fetchall()]
            except Exception as e:
                result["all_tables"] = [f"Error: {str(e)}"]
                
    except Exception as e:
        result["error"] = str(e)
    
    return result 