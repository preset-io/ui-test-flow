"""
Database initialization script.

Creates database tables and optionally seeds with initial data.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4


# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


async def create_sample_data(db):
    """Create sample organization and user for testing."""
    from uitestflow.server.auth import get_password_hash
    from uitestflow.server.database import Organization, User

    print("\nCreating sample data...")

    # Create organization
    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="Test Organization",
        plan="free",
        monthly_test_runs=100,
        storage_gb=1,
        retention_days=7,
        settings={},
    )
    db.add(org)

    # Create user
    user_id = uuid4()
    user = User(
        id=user_id,
        org_id=org_id,
        email="admin@example.com",
        name="Admin User",
        password_hash=get_password_hash("admin123"),
        role="admin",
    )
    db.add(user)

    await db.commit()

    print("\nSample data created:")
    print(f"  Organization: {org.name} (ID: {org_id})")
    print(f"  User: {user.email}")
    print("  Password: admin123")
    print("\nYou can now login with these credentials!")


async def main():
    """Initialize database."""
    from uitestflow.server.database import get_db_context, init_db, table_exists

    print("UITestFlow Database Initialization")
    print("=" * 50)

    # Check if tables already exist
    print("\nChecking existing tables...")
    if await table_exists("organizations"):
        print("\nWARNING: Database tables already exist!")
        response = input("Do you want to drop and recreate all tables? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

        from uitestflow.server.database import drop_db

        print("\nDropping existing tables...")
        await drop_db()
        print("Tables dropped.")

    # Create tables
    print("\nCreating database tables...")
    await init_db()
    print("Database tables created successfully!")

    # Ask if user wants sample data
    response = input("\nDo you want to create sample data? (yes/no): ")
    if response.lower() == "yes":
        async with get_db_context() as db:
            await create_sample_data(db)

    print("\n" + "=" * 50)
    print("Database initialization complete!")
    print("\nNext steps:")
    print("1. Start the server: python -m uitestflow.server.api")
    print("2. Visit API docs: http://localhost:8000/api/docs")
    print("3. Test login with the sample credentials above")


if __name__ == "__main__":
    asyncio.run(main())
