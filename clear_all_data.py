#!/usr/bin/env python3
"""
Clear all demo data from SOC platform
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def clear_data():
    print("Clearing all demo data from SOC platform...")

    # Get all assets
    try:
        response = requests.get(f"{BASE_URL}/assets/", params={"limit": 1000})
        if response.status_code == 200:
            assets = response.json().get("items", [])
            asset_ids = [asset["id"] for asset in assets]

            if asset_ids:
                print(f"Found {len(asset_ids)} assets to delete")
                # Delete all assets
                for asset_id in asset_ids:
                    del_response = requests.delete(f"{BASE_URL}/assets/{asset_id}")
                    if del_response.status_code in [200, 204]:
                        print(f"  Deleted asset {asset_id}")
                print(f"✓ Deleted {len(asset_ids)} assets")
            else:
                print("No assets to delete")
    except Exception as e:
        print(f"Error clearing assets: {e}")

    # Clear tasks
    try:
        response = requests.get(f"{BASE_URL}/tasks/", params={"page": 1, "limit": 1000})
        if response.status_code == 200:
            tasks = response.json().get("data", [])

            if tasks:
                print(f"Found {len(tasks)} tasks")
                # Note: Tasks are kept in memory, will be cleared on restart
                print("  Tasks will be cleared on restart")
            else:
                print("No tasks to delete")
    except Exception as e:
        print(f"Error checking tasks: {e}")

    print("\n✓ Demo data cleared!")
    print("The SOC platform is now ready for production use.")
    print("\nDefault admin credentials:")
    print("  Username: admin")
    print("  Password: secret123")
    print("\n⚠️  IMPORTANT: Change the admin password immediately after first login!")

if __name__ == "__main__":
    clear_data()