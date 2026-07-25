import gzip
import secrets
from logging import getLogger
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from domain.bulk_event import BulkEvent
from conf import container

app = FastAPI()
logger = getLogger("elasticsfake")
_http_basic = HTTPBasic(auto_error=False)


def _make_auth_dependency():
    conf = container.confdict
    enabled = conf.get("app.auth.enabled", False)
    if not enabled:
        def no_auth():
            return None
        return no_auth

    username = conf.get("app.auth.username", "elastic")
    password = conf.get("app.auth.password", "changeme")

    def verify(credentials: HTTPBasicCredentials = Depends(_http_basic)):
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Basic"},
            )
        ok = secrets.compare_digest(credentials.username, username) and \
             secrets.compare_digest(credentials.password, password)
        if not ok:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )

    return verify


_auth = _make_auth_dependency()

if container.confdict.get("app.gzip.enabled", True):
    @app.middleware("http")
    async def decompress_gzip(request: Request, call_next):
        if request.headers.get("content-encoding", "").lower() == "gzip":
            body = await request.body()
            try:
                decompressed = gzip.decompress(body)
            except Exception:
                return Response(content="Invalid gzip body", status_code=400)
            # Starlette caches the body in _body after the first read;
            # overwrite it so downstream handlers see the decompressed bytes.
            request._body = decompressed

        return await call_next(request)


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Elastic-Product"] = "Elasticsearch"
    return response


@app.head("/")
async def root_head(_: None = Depends(_auth)):
    return Response(status_code=200)


@app.get("/")
async def root_get(_: None = Depends(_auth)):
    return JSONResponse(
        content={
            "name": "ElasticsFake",
            "cluster_uuid": "",
            "version": {"number": "142.0.0", "build_flavor": "default"},
        }
    )


@app.head("/_cluster/health")
async def cluster_health_head(_: None = Depends(_auth)):
    return Response(status_code=200)


@app.get("/_cluster/health")
async def cluster_health_get(_: None = Depends(_auth)):
    return JSONResponse(
        content={
            "cluster_name": "docker-cluster",
            "status": "green",
            "timed_out": False,
            "number_of_nodes": 1,
            "number_of_data_nodes": 1,
            "active_primary_shards": 0,
            "active_shards": 0,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0,
            "delayed_unassigned_shards": 0,
            "number_of_pending_tasks": 0,
            "number_of_in_flight_fetch": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 100.0,
        }
    )


@app.get("/_license")
async def license_get(_: None = Depends(_auth)):
    return JSONResponse(
        content={
            "license": {
                "status": "active",
                "uid": "4012f721-8cbe-4309-b16d-665a24b67916",
                "type": "trial",
                "expiry_date_in_millis": 1756682583542,
            }
        }
    )


@app.post("/_bulk")
async def bulk(request: Request, _: None = Depends(_auth)):
    data = await request.body()
    data_str = data.decode("utf-8", errors="ignore")
    lines_received = [line for line in data_str.splitlines() if line.strip()]
    # Each event is sent in 2 lines
    # Sometimes empty lines are sent, we ignore them
    events_received_count = len(lines_received) // 2
    events_received = []

    # Here we build "events" objects out of the bulk data
    # each bulk message have 2 lines, first line with metadata
    # second line with the document.
    for idx in range(events_received_count):
        current_position = idx * 2
        event_metadata = lines_received[current_position]
        event_doc = lines_received[current_position + 1]
        events_received.append(BulkEvent(event_metadata, event_doc))

    try:
        container.bulk_handler.handle_bulk(events_received)
    except Exception:
        logger.exception("Failed to process %s events", events_received_count)
        items = [
            {
                "index": {
                    "status": 500,
                    "error": {
                        "type": "internal_error",
                        "reason": "bulk_handler failed to process this batch",
                    },
                }
            }
            for _ in events_received
        ]
        return JSONResponse({"took": 1, "errors": True, "items": items})

    logger.info("%s events processed", events_received_count)

    return JSONResponse({"took": 1, "errors": False, "items": []})
