import requests
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import time
from simple_chalk import chalk, green

# Set the base URL and pagination parameters
base_url = "http://localhost:8000/users/"
page_size = 10
total_users = 100


# Define the retry decorator
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(requests.RequestException),
)
def get_users(page: int, page_size: int):
    response = requests.get(base_url, params={"page": page, "page_size": page_size})
    response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx, 5xx)
    return response


def fetch_all_users():
    users = []
    for page in range(1, (total_users // page_size) + 2):
        try:
            response = get_users(page, page_size)
            page_users = response.json()
            print(f"Page {page}:")
            for user in page_users:
                print(user)
            users.extend(page_users)
        except requests.RequestException as e:
            print(f"Failed to get users for page {page}")
            print(f"Exception: {e}")
    return users


if __name__ == "__main__":
    start_time = time.time()
    fetch_all_users()
    end_time = time.time()
    end_time = time.time()
    run_time = chalk.bold(f"{end_time - start_time} seconds")
    print(green(f"Time taken to fetch all users: {run_time}"))
