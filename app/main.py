import logging

import pybreaker
from fastapi import FastAPI, HTTPException, Request

from app.api.routes import router
from app.core.logging_config import setup_logging

logger = logging.getLogger(__name__)
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

app = FastAPI()
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    setup_logging()
    logger.info("Application startup.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown.")


@app.middleware("http")
async def log_request(request: Request, call_next):
    logger.info(f"Received request: {request.method} {request.url}")

    body = await request.body()
    body_content = body.decode("utf-8")
    logger.info(
        "Request body: %s",
        body_content[:500] + ("..." if len(body_content) > 500 else ""),
    )
    logger.info("Request headers: %s", request.headers)
    logger.info("Client IP: %s", request.client.host)

    try:
        response = await breaker.call(lambda: call_next(request))
        logger.info(f"Response status: {response.status_code}")
    except pybreaker.CircuitBreakerError:
        logger.error("Circuit Breaker is open. Request failed.")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return response


@app.get("/")
async def root():
    try:
        logger.info("Root endpoint accessed.")
        return {"message": "Hello, World!"}
    except pybreaker.CircuitBreakerError:
        logger.error("Circuit Breaker is open. Request failed.")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
