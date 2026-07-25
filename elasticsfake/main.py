import uvicorn
from app.api import app
from conf import container


def _tls_kwargs() -> dict:
    conf = container.confdict
    if not conf.get("app.tls.enabled", False):
        return {}

    return {
        "ssl_certfile": conf["app.tls.certfile"],
        "ssl_keyfile": conf["app.tls.keyfile"],
    }


if __name__ == "__main__":
    uvicorn.run(
        app, host="0.0.0.0", port=9200, limit_concurrency=1000, **_tls_kwargs()
    )
