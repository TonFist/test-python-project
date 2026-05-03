from http import HTTPStatus

from app.router import Response, Router


router = Router()
api_router = Router()
router.mount("/api", api_router)


@router.get("/")
def index(_request):
    return Response.text("Hello from router")


@router.get("/health")
def health(_request):
    return Response.json({"status": "ok"})


@api_router.get("/health")
def api_health(_request):
    return Response.json({"status": "ok", "scope": "api"})


@router.post("/echo")
def echo(request):
    if not request.body:
        return Response.text("Missing body", status=HTTPStatus.BAD_REQUEST)
    return Response.text(request.body.decode("utf-8"))


@api_router.post("/echo")
def api_echo(request):
    if not request.body:
        return Response.json({"error": "Missing body"}, status=HTTPStatus.BAD_REQUEST)
    return Response.json({"echo": request.body.decode("utf-8")})
