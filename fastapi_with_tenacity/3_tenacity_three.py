import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    wait_random_exponential,
)
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

# Set the base URL and pagination parameters
base_url = "http://localhost:8000/users/"
page_size = 10
total_users = 100
max_concurrent_requests = 20  # Adjusted for concurrency limits


### We don't need this, should be handled automatically
# request_rate_limit = 5  # 4 requests per second
# delay_between_requests = 1 / request_rate_limit  # Delay to respect rate limit


def log_attempt_number(retry_state):
    """return the result of the last call attempt"""
    logger.error(f"Retrying: {retry_state.attempt_number}...")


# Define the retry decorator with exponential backoff
@retry(
    stop=stop_after_attempt(20),
    # wait=wait_exponential(multiplier=1, min=4, max=10),  # Exponential backoff with a minimum of 4 seconds and a maximum of 10 seconds
    wait=wait_random_exponential(multiplier=2, max=30),  # This is more robust way
    retry=retry_if_exception_type(requests.RequestException),
    after=log_attempt_number,
)
def get_users(page: int, page_size: int):
    """Fetches users for a given page with retry logic."""
    logger.info(f"Geting users, page: {page}, page_size: {page_size} ")
    response = requests.get(base_url, params={"page": page, "page_size": page_size})
    response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx, 5xx)
    logger.info(f"Success geting users, page: {page}, page_size: {page_size} ")
    return response


def fetch_page(page: int):
    """Fetches a single page of users, with retry logic handling failures."""
    try:
        response = get_users(page, page_size)
        return (page, response.json())
    except requests.RequestException as e:
        print(f"Failed to get users for page {page}")
        print(f"Exception: {e}")
        return (page, None)


def fetch_all_users():
    """Fetches all users using concurrent requests with retry logic."""
    users = []
    with ThreadPoolExecutor(max_workers=max_concurrent_requests) as executor:
        # Submit tasks for each page
        futures = [
            executor.submit(fetch_page, page)
            for page in range(1, (total_users // page_size) + 2)
        ]

        for future in as_completed(futures):
            page, result = future.result()
            if result:
                print(f"Page {page}:")
                for user in result:
                    print(user)
                users.extend(result)
            # time.sleep(delay_between_requests)  # Delay between requests to avoid hitting rate limits
    return users


if __name__ == "__main__":
    start_time = time.time()
    fetch_all_users()
    end_time = time.time()
    print(f"Time taken to fetch all users: {end_time - start_time} seconds")
