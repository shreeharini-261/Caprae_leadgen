from flask import Flask
import sys
import os
from sqlalchemy import text

# Add parent directory to path to run script independently
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.lead_model import db
from models.audit_log_model import ensure_audit_log_infrastructure

def recreate_database():
    """Drop all tables and recreate them"""
    with app.app_context():
        # Get engine connection
        connection = db.engine.connect()
        
        # Disable foreign key checks temporarily
        # Drop existing tables with CASCADE to handle dependencies
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        
        # Grant privileges (needed in PostgreSQL after recreating the schema)
        connection.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        connection.execute(text("GRANT ALL ON SCHEMA public TO public"))
        
        # Commit the transaction
        connection.commit()
        
        print("Dropped all tables")
        
        # Create tables with new schema
        db.create_all()
        
        # Set up audit log infrastructure
        ensure_audit_log_infrastructure(db)
        
        print("Created all tables with new schema")
        
        # Close connection
        connection.close()
    
    print("Database tables recreated successfully!")

if __name__ == "__main__":
    recreate_database() 