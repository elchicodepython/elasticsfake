from logging import getLogger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from conf import container

app = FastAPI()
logger = getLogger("elasticsfake")


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Elastic-Product"] = "Elasticsearch"
    return response


@app.head("/")
async def root_head():
    return Response(status_code=200)  # Solo OK, sin contenido


@app.get("/")
async def root_get():
    return JSONResponse(
        content={
            "name": "ElasticsFake",
            "cluster_uuid": "",
            "version": {"number": "142.0.0", "build_flavor": "default"},
        }
    )


# HEAD /_cluster/health → solo 200 OK
@app.head("/_cluster/health")
async def cluster_health_head():
    return Response(status_code=200)


# GET /_cluster/health → devuelve un estado de cluster compatible
@app.get("/_cluster/health")
async def cluster_health_get():
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
async def license_get():
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
async def bulk(request: Request):
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
        events_received.append({"meta": event_metadata, "doc": event_doc})

    container.bulk_handler.handle_bulk(events_received)
    logger.info("%s events processed", events_received_count)

    return JSONResponse({"took": 1, "errors": False, "items": []})
