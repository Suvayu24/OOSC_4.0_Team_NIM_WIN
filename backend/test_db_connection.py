"""
Standalone connectivity check -- no FastAPI, no routers. Run this directly
to see the REAL exception behind the generic 500 on /demo/seed:

    python test_db_connection.py

If this fails, the fix is almost always one of:
  - `pip install -r requirements.txt` again (dnspython was missing)
  - Atlas -> Network Access -> add your current IP (or 0.0.0.0/0 for a demo)
  - Atlas -> Database Access -> confirm the user/password in .env match exactly
  - the cluster is paused (free-tier Atlas clusters auto-pause after inactivity)
"""
import asyncio

from config import settings
from db import client


async def main():
    print(f"Connecting to: {settings.mongo_uri.split('@')[-1]}")  # hide credentials in the printout
    try:
        info = await client.server_info()
        print("Connected OK. Server version:", info.get("version"))
        dbs = await client.list_database_names()
        print("Databases visible to this user:", dbs)
    except Exception as e:
        print(f"\nCONNECTION FAILED: {type(e).__name__}: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
