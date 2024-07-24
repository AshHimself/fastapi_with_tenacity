import requests

# Set the base URL and pagination parameters
base_url = "http://localhost:8000/users/"
page_size = 3
total_users = 100

# Loop through pages
for page in range(1, (total_users // page_size) + 2):
    response = requests.get(base_url, params={"page": page, "page_size": page_size})

    # Check if the request was successful
    if response.status_code == 200:
        users = response.json()
        print(f"Page {page}:")
        for user in users:
            print(user)
    else:
        print(f"Failed to get users for page {page}")
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.text}")
