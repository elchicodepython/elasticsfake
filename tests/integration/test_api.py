import gzip
import json
import pytest


BULK_BODY = (
    '{"index":{"_index":"test-index","_id":"1"}}\n'
    '{"message":"hello world","level":"INFO"}\n'
    '{"index":{"_index":"test-index","_id":"2"}}\n'
    '{"message":"second event","level":"DEBUG"}\n'
)


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

def test_root_get_returns_cluster_info(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "ElasticsFake"
    assert "version" in body
    assert body["version"]["number"]


def test_root_head_returns_200(client):
    r = client.head("/")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Cluster health
# ---------------------------------------------------------------------------

def test_cluster_health_get_returns_green(client):
    r = client.get("/_cluster/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "green"
    assert body["timed_out"] is False


def test_cluster_health_head_returns_200(client):
    r = client.head("/_cluster/health")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# License
# ---------------------------------------------------------------------------

def test_license_returns_active(client):
    r = client.get("/_license")
    assert r.status_code == 200
    body = r.json()
    assert body["license"]["status"] == "active"


# ---------------------------------------------------------------------------
# X-Elastic-Product header present on all responses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,path", [
    ("GET", "/"),
    ("GET", "/_cluster/health"),
    ("GET", "/_license"),
])
def test_x_elastic_product_header(client, method, path):
    r = client.request(method, path)
    assert r.headers.get("x-elastic-product") == "Elasticsearch"


# ---------------------------------------------------------------------------
# Bulk endpoint — plain body
# ---------------------------------------------------------------------------

def test_bulk_plain_returns_success(client):
    r = client.post("/_bulk", content=BULK_BODY,
                    headers={"Content-Type": "application/x-ndjson"})
    assert r.status_code == 200
    body = r.json()
    assert body["errors"] is False


def test_bulk_plain_dispatches_events(client, mock_bulk_handler):
    client.post("/_bulk", content=BULK_BODY,
                headers={"Content-Type": "application/x-ndjson"})
    events = mock_bulk_handler.captured
    assert len(events) > 0
    assert len(events) == 2
    assert events[0].index == "test-index"
    assert events[0].doc["message"] == "hello world"
    assert events[1].doc["message"] == "second event"


# ---------------------------------------------------------------------------
# Bulk endpoint — gzip-compressed body
# ---------------------------------------------------------------------------

def test_bulk_gzip_returns_success(client):
    compressed = gzip.compress(BULK_BODY.encode())
    r = client.post(
        "/_bulk",
        content=compressed,
        headers={
            "Content-Type": "application/x-ndjson",
            "Content-Encoding": "gzip",
        },
    )
    assert r.status_code == 200
    assert r.json()["errors"] is False


def test_bulk_gzip_dispatches_same_events_as_plain(client, mock_bulk_handler):
    compressed = gzip.compress(BULK_BODY.encode())
    client.post(
        "/_bulk",
        content=compressed,
        headers={
            "Content-Type": "application/x-ndjson",
            "Content-Encoding": "gzip",
        },
    )
    events = mock_bulk_handler.captured
    assert len(events) == 2
    assert events[0].index == "test-index"


def test_bulk_invalid_gzip_returns_400(client):
    r = client.post(
        "/_bulk",
        content=b"this is not gzip data",
        headers={
            "Content-Type": "application/x-ndjson",
            "Content-Encoding": "gzip",
        },
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def test_auth_no_credentials_returns_401(auth_client):
    r = auth_client.get("/", auth=None)
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Basic"


def test_auth_wrong_password_returns_401(auth_client):
    r = auth_client.get("/", auth=("elastic", "wrongpass"))
    assert r.status_code == 401


def test_auth_wrong_username_returns_401(auth_client):
    r = auth_client.get("/", auth=("admin", "changeme"))
    assert r.status_code == 401


def test_auth_correct_credentials_passes(auth_client):
    r = auth_client.get("/", auth=("elastic", "changeme"))
    assert r.status_code == 200


def test_auth_correct_credentials_bulk(auth_client, mock_bulk_handler):
    r = auth_client.post(
        "/_bulk",
        content=BULK_BODY,
        headers={"Content-Type": "application/x-ndjson"},
        auth=("elastic", "changeme"),
    )
    assert r.status_code == 200


def test_auth_disabled_no_credentials_passes(client):
    r = client.get("/")
    assert r.status_code == 200
