#!/usr/bin/env python3
"""Test script to verify location creation in the database."""

import sys
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 1)[0])

from core.db.db import init_db, create_db_and_tables
from core.db.db_access import get_or_create_location, request_all
from core.model.data_models import Location
from pydantic import PostgresDsn

# Initialize DB
db_url = PostgresDsn.build(
    scheme="postgresql",
    username="postgres",
    password="password",
    host="localhost",
    port=5432,
    path="example_db"
)

print(f"Connecting to: {db_url}")
init_db(db_url)
create_db_and_tables()

print("\n=== Testing Location Creation ===\n")

# Test 1: Create a location
test_names = [
    "Rathaus",
    "Plenarsaal",
    "Bezirksausschuss Altstadt-Lehel",
]

for name in test_names:
    print(f"Creating location: '{name}'")
    location = get_or_create_location(name)
    print(f"  -> id: {location.id}")
    print(f"  -> db_id: {location.db_id}")
    print(f"  -> name: {location.name}")
    print()

# Test 2: Query all locations
print("=== All Locations in DB ===\n")
all_locations = request_all(Location)
print(f"Found {len(all_locations)} locations:\n")
for loc in all_locations:
    print(f"  - {loc.name} (id: {loc.id}, db_id: {loc.db_id})")

print("\n=== Test Complete ===")
