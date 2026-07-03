# FastAPI Fundamentals

## What is FastAPI?

FastAPI is a modern Python web framework for building APIs. It is built on top of Starlette (for the web handling) and Pydantic (for data validation), and is designed to let developers write APIs quickly while automatically generating interactive documentation and validating incoming request data.

## Why FastAPI is Popular for ML Model Serving

FastAPI is widely used to wrap trained machine learning models as REST APIs because it is fast (built on asynchronous Python, using ASGI rather than the older WSGI standard), has built-in data validation that catches malformed requests before they ever reach the model, and automatically generates interactive API documentation (via Swagger UI) with no extra work required.

## Basic Application Structure

A minimal FastAPI application defines an app object and one or more route handlers:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

Running this with a server like `uvicorn app:app --reload` starts a local development server, and visiting `/docs` in a browser shows the auto-generated interactive documentation for all defined endpoints.

## Request and Response Validation with Pydantic

FastAPI uses Pydantic models to define the expected shape of request and response data. A Pydantic model is a Python class where each attribute has a declared type, and FastAPI automatically validates incoming JSON against it, returning a clear error if the data doesn't match.

```python
from pydantic import BaseModel

class Transaction(BaseModel):
    amount: float
    merchant: str
    timestamp: str

@app.post("/predict")
def predict(transaction: Transaction):
    # transaction.amount, transaction.merchant, etc. are now
    # validated and type-checked automatically
    prediction = run_model(transaction)
    return {"fraud_probability": prediction}
```

If a client sends a request missing the `amount` field or sends a string where a float is expected, FastAPI rejects the request automatically before the handler function even runs, which prevents a whole category of bugs where malformed input silently reaches a model and produces a nonsensical prediction.

## Path Parameters and Query Parameters

FastAPI distinguishes between path parameters (part of the URL itself, like `/predictions/{transaction_id}`) and query parameters (appended after a `?`, like `/predictions?limit=10`). Both are declared as function arguments and are automatically validated and converted to the correct Python type.

## Dependency Injection

FastAPI has a built-in dependency injection system, commonly used to load a trained model once when the application starts rather than reloading it on every request. This is important for ML serving specifically, since loading a model from disk can be slow, and reloading it on every prediction request would make the API unacceptably slow.

```python
model = None

@app.on_event("startup")
def load_model():
    global model
    model = load_trained_model("model.pkl")
```

## Async Support

Because FastAPI is built on ASGI, route handlers can be defined as `async def` functions, allowing the server to handle many concurrent requests efficiently without blocking on slow operations like network calls or database queries. This matters for production ML serving, where a single API instance may need to handle many simultaneous prediction requests.

## Error Handling

FastAPI allows raising `HTTPException` with a specific status code and message to return meaningful errors to clients, such as returning a 422 status code when input validation fails, or a 503 status code if the underlying model isn't loaded yet.
