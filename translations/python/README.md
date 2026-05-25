# ApexKit Python SDK

A Python client for the ApexKit API.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from apexkit import ApexKit

# Initialize the client
apex = ApexKit("http://localhost:5000")

# Login
auth_res = apex.auth.login("admin@example.com", "password")
print(f"Logged in as: {auth_res['user']['email']}")

# List collections
collections = apex.admins.list_collections()
for col in collections:
    print(f"Collection: {col['name']}")

# Working with records
posts = apex.collection("posts")
records = posts.list({"page": 1, "per_page": 10})
for record in records['items']:
    print(f"Record: {record['id']}")
```

## Realtime (WebSocket)

```python
import asyncio
from apexkit import ApexKitRealtimeWSClient

async def main():
    realtime = ApexKitRealtimeWSClient("http://localhost:5000", token="YOUR_TOKEN")

    def on_event(msg):
        print("Received event:", msg)

    realtime.on_event(on_event)

    # Run connection in background
    asyncio.create_task(realtime.connect())

    # Subscribe to changes
    await asyncio.sleep(1) # wait for connection
    await realtime.subscribe({"collectionId": 1})

    # Keep running
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```
