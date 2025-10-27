import os
import httpx
import traceback
from typing import Dict
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from app.log.logger_config import setup_logging

logger = setup_logging(__name__)

load_dotenv()

SERVICE_A_NAME = os.getenv("SERVICE_A_NAME")
SERVICE_B_NAME = os.getenv("SERVICE_B_NAME")
SERVICE_C_NAME = os.getenv("SERVICE_C_NAME")

SERVICE_A_URL = os.getenv("SERVICE_A_URL")
SERVICE_B_URL = os.getenv("SERVICE_B_URL")
SERVICE_C_URL = os.getenv("SERVICE_C_URL")

TIMEOUT_SECONDS = os.getenv("TIMEOUT_SECONDS")

# cấu hình mapping service (tên → URL)
SERVICE_MAP: Dict[str, str] = {
    SERVICE_A_NAME: SERVICE_A_URL,
    SERVICE_B_NAME: SERVICE_B_URL,
    SERVICE_C_NAME: SERVICE_C_URL,
}

async def forward_to_service(service_name: str, request: Request, full_path: str):
    if service_name not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    target_base = SERVICE_MAP[service_name]
    target_url = f"{target_base}/{full_path}"
    logger.info(f"Forwarding request to {target_url}")
    
    method = request.method
    headers = dict(request.headers)
    # bỏ header host để tránh lỗi dịch vụ đích
    headers.pop("host", None)

    # lấy body nếu có
    body = await request.body()
    params = dict(request.query_params)
    
    timeout = httpx.Timeout(float(TIMEOUT_SECONDS))

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                content=body
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail=f"Upstream service timeout: {exc}")
        except httpx.RequestError as exc:
            traceback_str = traceback.format_exc()
            logger.error(f"Request to {target_url} failed: {exc}\n{traceback_str}")
            
            raise HTTPException(status_code=502, detail=f"Bad gateway: {exc}")

    return resp
