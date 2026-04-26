#!/usr/bin/env python3
"""
Direct PostgreSQL migration script using psycopg2
This will add the approval columns to your database
"""

import psycopg2
import os
from datetime import datetime

def run_postgresql_migration():
    """Connect directly to PostgreSQL and add the approval columns"""
    
    # Database connection settings (from your config.py)
    db_config = {
        'host': 'localhost',
        'database': 'flaskapp',
        'user': 'postgres',
        'password': 'postgres',
        'port': '5432'
    }
    
    try:
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL successfully")
        
        # Check existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            AND table_schema = 'public'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📊 Existing columns: {existing_columns}")
        
        # Add is_approved column
        if 'is_approved' not in existing_columns:
            print("➕ Adding is_approved column...")
            cursor.execute('ALTER TABLE "user" ADD COLUMN is_approved BOOLEAN DEFAULT FALSE NOT NULL')
            print("✅ Added is_approved column")
        else:
            print("ℹ️ is_approved column already exists")
        
        # Add approval_requested_at column
        if 'approval_requested_at' not in existing_columns:
            print("➕ Adding approval_requested_at column...")
            cursor.execute('ALTER TABLE "user" ADD COLUMN approval_requested_at TIMESTAMP')
            print("✅ Added approval_requested_at column")
        else:
            print("ℹ️ approval_requested_at column already exists")
        
        # Add approved_at column
        if 'approved_at' not in existing_columns:
            print("➕ Adding approved_at column...")
            cursor.execute('ALTER TABLE "user" ADD COLUMN approved_at TIMESTAMP')
            print("✅ Added approved_at column")
        else:
            print("ℹ️ approved_at column already exists")
        
        # Add approved_by column
        if 'approved_by' not in existing_columns:
            print("➕ Adding approved_by column...")
            cursor.execute('ALTER TABLE "user" ADD COLUMN approved_by INTEGER')
            print("✅ Added approved_by column")
        else:
            print("ℹ️ approved_by column already exists")
        
        # Update existing users
        print("📝 Updating existing users...")
        cursor.execute("""
            UPDATE "user" 
            SET is_approved = TRUE, 
                approval_requested_at = %s, 
                approved_at = %s 
            WHERE is_approved = FALSE OR is_approved IS NULL
        """, (datetime.utcnow(), datetime.utcnow()))
        
        updated_count = cursor.rowcount
        print(f"✅ Updated {updated_count} existing users to maintain access")
        
        # Commit changes
        conn.commit()
        print("💾 Changes committed to database")
        
        # Verify the changes
        cursor.execute('SELECT id, username, is_approved FROM "user" LIMIT 3')
        users = cursor.fetchall()
        print("\n📋 Sample user data:")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Approved: {user[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check database name: 'flaskapp'")
        print("3. Check username: 'postgres'")
        print("4. Check password: 'postgres'")
        print("5. Check host: 'localhost'")
        print("6. Check port: '5432'")
        return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting PostgreSQL migration for user approval fields...")
    print("=" * 60)
    
    success = run_postgresql_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📋 Summary of changes:")
        print("  • Added is_approved column (BOOLEAN)")
        print("  • Added approval_requested_at column (TIMESTAMP)")
        print("  • Added approved_at column (TIMESTAMP)")
        print("  • Added approved_by column (INTEGER)")
        print("  • Updated existing users to maintain access")
        print("\n🚀 Next steps:")
        print("  1. Restart your Flask application")
        print("  2. Test the approval workflow:")
        print("     - Register a new user (should show 'approval pending')")
        print("     - Try to login (should show approval required)")
        print("     - Login as admin to approve the user")
        print("     - Approved user can now login")
    else:
        print("\n❌ Migration failed.")
        print("Please check your PostgreSQL configuration and try again.")
