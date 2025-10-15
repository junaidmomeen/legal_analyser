from fastapi import HTTPException, Request, status
import os


async def enforce_content_length_limit(request: Request) -> None:
    """Early guard: reject requests with Content-Length exceeding configured max size.
    Relies on client setting Content-Length; deeper checks still occur later.
    """
    max_mb = float(os.getenv("MAX_FILE_SIZE_MB", os.getenv("MAX_FILE_SIZE", "50")))
    max_bytes = int(max_mb * 1024 * 1024)
    content_length = request.headers.get("content-length")
    if content_length is None:
        return

    try:
        if int(content_length) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Max {max_mb:.0f}MB",
            )
    except ValueError:
        return
