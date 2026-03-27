import time

from fastapi import FastAPI, Request

from app.core.logging import get_logger

logger = get_logger(__name__)


async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info("%s %s - %.4fs", request.method, request.url.path, process_time)
    return response



def add_middlewares(app: FastAPI) -> None:
    app.middleware("http")(add_process_time_header)
