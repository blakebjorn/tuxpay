from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from fastapi import FastAPI

from modules import config
from modules.authentication import TokenAuthBackend
from views.users import router as users_router
from views.admin_dashboard import router as admin_dashboard_router
from views.admin_invoice import router as admin_invoice_router
from views.admin_payment import router as admin_payment_router
from views.invoice import router as invoice_router
from views.utils import router as utils_router
from views.payment import watch_payment
from views.payment import router as payment_router
from views.api_models import tags_metadata


def make_application():
    middleware = [
        Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*']),
        Middleware(AuthenticationMiddleware, backend=TokenAuthBackend())
    ]

    app = FastAPI(debug=config.check("debug"),
                  title="TuxPay",
                  description="TuxPay Payment API Server",
                  version="0.0.1",
                  openapi_tags=tags_metadata,
                  middleware=middleware,
                  routes=[
                      WebSocketRoute("/api/payment", watch_payment),
                      Route("/tuxpay.js", lambda x: FileResponse("sdk/dist/tuxpay.js")),
                      Route("/tuxpay.js.map", lambda x: FileResponse("sdk/dist/tuxpay.js.map")),
                      Route("/payment", lambda x: FileResponse("views/payment.html")),
                      Mount("/admin", app=StaticFiles(directory='admin/dist', html=True), name='admin'),
                      Route("/", lambda x: FileResponse("admin/dist/index.html")),
                  ])
    app.include_router(users_router)
    app.include_router(admin_dashboard_router)
    app.include_router(admin_invoice_router)
    app.include_router(admin_payment_router)
    app.include_router(payment_router)
    app.include_router(invoice_router)
    app.include_router(utils_router)
    return app
