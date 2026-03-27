from typing import Any



def payload(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}



def ok(message: str = "success", data: Any = None) -> dict[str, Any]:
    return payload(200, message, data)



def error(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return payload(code, message, data)
