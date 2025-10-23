# Temporary admin endpoint for schema migration
@router.post("/admin/migrate-user-schema")
async def migrate_user_schema():
    """One-time migration to fix user schema"""
    try:
        result = await database.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name LIKE '%password%';"))
        current_columns = [row[0] for row in result]
        
        if 'password' in current_columns and 'hashed_password' not in current_columns:
            await database.execute(text("ALTER TABLE users RENAME COLUMN password TO hashed_password;"))
            return {"success": True, "message": "Renamed password column to hashed_password"}
        else:
            return {"success": True, "message": "Schema already correct", "columns": current_columns}
    except Exception as e:
        return {"success": False, "error": str(e)}
