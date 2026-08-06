"""Tests for the FastAPI / Flask / Django REST Python API surface extractor."""

from conftest import extract_all

ROUTES = """
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CreateAccountRequest(BaseModel):
    customer_id: str
    initial_balance: float = 0.0


@router.get("/api/accounts/{account_id}")
def get_account(account_id: str) -> AccountResponse:
    return None


@router.post("/api/accounts")
async def create_account(request: CreateAccountRequest):
    return None


@router.get("/api/accounts")
def list_accounts(page: int = 1, active: bool = True):
    return None
"""


def endpoints_by_handler(endpoints):
    return {e.handler_name: e for e in endpoints}


def test_fastapi_routes_and_methods_are_extracted(python_extractor):
    endpoints, _, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["get_account"].http_method == "GET"
    assert by_handler["get_account"].path == "/api/accounts/{account_id}"
    assert by_handler["create_account"].http_method == "POST"


def test_path_template_params_are_classified_as_path(python_extractor):
    """A parameter named in the route template binds from the path, not the body."""
    endpoints, _, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_handler = endpoints_by_handler(endpoints)

    account_id = by_handler["get_account"].parameters[0]
    assert account_id.name == "account_id"
    assert account_id.source == "path"


def test_scalar_params_absent_from_path_are_query_params(python_extractor):
    endpoints, _, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_handler = endpoints_by_handler(endpoints)

    sources = {p.name: p.source for p in by_handler["list_accounts"].parameters}
    assert sources == {"page": "query", "active": "query"}


def test_model_typed_param_is_treated_as_request_body(python_extractor):
    endpoints, _, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_handler = endpoints_by_handler(endpoints)

    create = by_handler["create_account"]
    assert create.request_body_type == "CreateAccountRequest"
    assert create.parameters[0].source == "body"


def test_path_params_do_not_leak_into_request_body_type(python_extractor):
    """A GET with only a path param has no request body."""
    endpoints, _, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["get_account"].request_body_type is None


def test_return_annotation_is_captured(python_extractor):
    endpoints, _, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["get_account"].return_type == "AccountResponse"


def test_pydantic_model_fields_and_optionality(python_extractor):
    _, types, _ = extract_all(python_extractor, ROUTES, "routes.py")
    by_name = {t.name: t for t in types}

    model = by_name["CreateAccountRequest"]
    assert "BaseModel" in model.parent_types

    fields = {f.name: (f.type, f.required) for f in model.fields}
    assert fields["customer_id"] == ("str", True)
    # A field with a default is optional.
    assert fields["initial_balance"][1] is False


FLASK_ROUTES = """
from flask import Blueprint

bp = Blueprint("accounts", __name__)


@bp.route("/api/accounts/<account_id>", methods=["GET"])
def get_account(account_id):
    return None
"""


def test_flask_angle_bracket_path_params_are_classified(python_extractor):
    endpoints, _, _ = extract_all(python_extractor, FLASK_ROUTES, "views.py")

    assert len(endpoints) == 1
    param = endpoints[0].parameters[0]
    assert param.name == "account_id"
    assert param.source == "path"


def test_module_without_routes_yields_no_endpoints(python_extractor):
    endpoints, _, _ = extract_all(python_extractor, "def helper(x):\n    return x\n", "utils.py")
    assert endpoints == []


AIOHTTP_ROUTES = """
from aiohttp import web


async def api_config_schema(request):
    return web.json_response({})


async def handle_migrate_cleanup(request):
    return web.json_response({})


def setup_routes(app):
    app.router.add_get("/api/config/schema", api_config_schema)
    app.router.add_delete("/api/apps/{name}/migrate-cleanup", handlers.handle_migrate_cleanup)
    app.router.add_route("POST", "/api/apps/{name}/deploy", handle_deploy)
"""


def test_aiohttp_add_method_calls_are_extracted(python_extractor):
    """aiohttp registers routes via router.add_get(path, handler), not decorators."""
    endpoints, _, _ = extract_all(python_extractor, AIOHTTP_ROUTES, "gateway.py")
    by_path = {e.path: e for e in endpoints}

    assert by_path["/api/config/schema"].http_method == "GET"
    assert by_path["/api/config/schema"].handler_name == "api_config_schema"
    assert by_path["/api/apps/{name}/migrate-cleanup"].http_method == "DELETE"


def test_aiohttp_dotted_handler_reference_uses_final_name(python_extractor):
    """A handler passed as `handlers.foo` is recorded by its function name."""
    endpoints, _, _ = extract_all(python_extractor, AIOHTTP_ROUTES, "gateway.py")
    by_path = {e.path: e for e in endpoints}

    assert by_path["/api/apps/{name}/migrate-cleanup"].handler_name == "handle_migrate_cleanup"


def test_aiohttp_handler_defined_in_module_recovers_path_params(python_extractor):
    """When the handler is defined locally, its params are resolved and classified."""
    source = '''
from aiohttp import web


async def get_app(request, name: str):
    return web.json_response({})


def setup_routes(app):
    app.router.add_get("/api/apps/{name}", get_app)
'''
    endpoints, _, _ = extract_all(python_extractor, source, "gateway.py")

    assert len(endpoints) == 1
    name = [p for p in endpoints[0].parameters if p.name == "name"][0]
    assert name.source == "path"
