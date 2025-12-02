from app import app

client = app.test_client()

try:
    response = client.get('/')
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.data.decode('utf-8')}")
except Exception as e:
    print(f"Runtime Error: {e}")
    import traceback
    traceback.print_exc()
