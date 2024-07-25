from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from faker import Faker
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
import time
from asyncio import Semaphore, TimeoutError
from collections import defaultdict

app = FastAPI()
faker = Faker()

class User(BaseModel):
    id: int
    name: str
    email: str
    address: str
    phone: str

# Limits
MAX_CONCURRENT_REQUESTS = 5
REQUESTS_PER_SECOND = 4
DAILY_REQUEST_LIMIT = 2000

# Track request timestamps
request_timestamps = defaultdict(list)
semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)

# Counter for tracking requests
request_counter = 0
counter_lock = Semaphore(1)  # To ensure thread-safe operations on the counter

def generate_fake_user(user_id: int) -> User:
    return User(
        id=user_id,
        name=faker.name(),
        email=faker.email(),
        address=faker.address(),
        phone=faker.phone_number()
    )

@app.get("/users/", response_model=List[User])
def get_users(page: int = 1, page_size: int = 3):
    total_users = 100
    start = (page - 1) * page_size
    end = start + page_size
    users = [generate_fake_user(user_id) for user_id in range(start + 1, min(end + 1, total_users + 1))]
    return users

class ThrottlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global request_counter
        client_ip = request.client.host
        current_time = time.time()
        
        # Enforce daily request limit
        if len(request_timestamps[client_ip]) >= DAILY_REQUEST_LIMIT:
            # Remove old requests to ensure the limit is based on the last 24 hours
            request_timestamps[client_ip] = [ts for ts in request_timestamps[client_ip] if current_time - ts < 86400]
            if len(request_timestamps[client_ip]) >= DAILY_REQUEST_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Daily request limit reached. Please try again tomorrow."}
                )

        # Enforce per-second rate limit
        if len(request_timestamps[client_ip]) > 0:
            if current_time - request_timestamps[client_ip][-1] < 1 / REQUESTS_PER_SECOND:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please wait before making another request."}
                )
        
        # Enforce concurrency limit
        try:
            async with semaphore:
                # Update request timestamps
                request_timestamps[client_ip].append(current_time)
                
                # Increment request counter
                async with counter_lock:
                    # nonlocal request_counter
                    request_counter += 1
                
                # Process the request
                response = await call_next(request)
                return response
        except TimeoutError:
            return JSONResponse(
                status_code=429,
                content={"detail": "Concurrency limit reached. Please try again later."}
            )

app.add_middleware(ThrottlingMiddleware)

@app.get("/request_count")
def get_request_count():
    return {"request_count": request_counter}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
