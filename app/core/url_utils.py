from fastapi import Request


def build_absolute_url(path: str, *, request: Request, configured_base: str = "") -> str:
    base_url = configured_base.strip() or str(request.base_url)
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
