from fastapi import APIRouter, Request, Response
from app.services.forward_service import forward_to_service

router = APIRouter()

@router.api_route("/{service_name}/{full_path:path}", methods=["GET","POST","PUT","DELETE","PATCH"])
async def proxy(service_name: str, full_path: str, request: Request):
    resp = await forward_to_service(service_name, request, full_path)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers)
    )
