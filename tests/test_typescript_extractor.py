"""Tests for the NestJS / Express TypeScript API surface extractor."""

from conftest import extract_all

NESTJS = """
import { Controller, Get, Post, Param, Body } from "@nestjs/common";

export interface CreateAccountRequest {
  customerId: string;
  initialBalance?: number;
}

@Controller("api/accounts")
export class AccountController {
  @Get(":accountId")
  getAccount(@Param("accountId") accountId: string) {}

  @Post()
  createAccount(@Body() request: CreateAccountRequest) {}
}
"""


def endpoints_by_handler(endpoints):
    return {e.handler_name: e for e in endpoints}


def test_nestjs_method_decorators_are_discovered(typescript_extractor):
    """Method decorators are siblings of method_definition, not children."""
    endpoints, _, _ = extract_all(typescript_extractor, NESTJS, "account.controller.ts")
    by_handler = endpoints_by_handler(endpoints)

    assert "getAccount" in by_handler
    assert "createAccount" in by_handler


def test_controller_path_is_joined_with_method_path(typescript_extractor):
    endpoints, _, _ = extract_all(typescript_extractor, NESTJS, "account.controller.ts")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["getAccount"].path == "/api/accounts/:accountId"


def test_bare_post_decorator_maps_to_controller_root(typescript_extractor):
    endpoints, _, _ = extract_all(typescript_extractor, NESTJS, "account.controller.ts")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["createAccount"].path == "/api/accounts"
    assert by_handler["createAccount"].http_method == "POST"


def test_param_decorator_sets_path_source(typescript_extractor):
    endpoints, _, _ = extract_all(typescript_extractor, NESTJS, "account.controller.ts")
    by_handler = endpoints_by_handler(endpoints)

    param = by_handler["getAccount"].parameters[0]
    assert param.name == "accountId"
    assert param.source == "path"


def test_body_decorator_survives_framework_param_skiplist(typescript_extractor):
    """`@Body() request` must not be dropped for being named `request`."""
    endpoints, _, _ = extract_all(typescript_extractor, NESTJS, "account.controller.ts")
    by_handler = endpoints_by_handler(endpoints)

    create = by_handler["createAccount"]
    assert create.request_body_type == "CreateAccountRequest"
    assert create.parameters[0].source == "body"


def test_interface_fields_and_optional_markers(typescript_extractor):
    _, types, _ = extract_all(typescript_extractor, NESTJS, "account.controller.ts")
    by_name = {t.name: t for t in types}

    iface = by_name["CreateAccountRequest"]
    assert iface.kind == "interface"

    fields = {f.name: (f.type, f.required) for f in iface.fields}
    assert fields["customerId"] == ("string", True)
    # `initialBalance?` is optional.
    assert fields["initialBalance"][1] is False


EXPRESS = """
const router = express.Router();

router.get("/api/health", (req, res) => {
  res.send("ok");
});

router.post("/api/accounts", createAccountHandler);
"""


def test_express_router_routes_are_extracted(typescript_extractor):
    endpoints, _, _ = extract_all(typescript_extractor, EXPRESS, "routes.ts")

    routes = {(e.http_method, e.path) for e in endpoints}
    assert ("GET", "/api/health") in routes
    assert ("POST", "/api/accounts") in routes


def test_express_req_res_params_are_not_api_surface(typescript_extractor):
    """Undecorated (req, res) handler args are framework plumbing, not parameters."""
    endpoints, _, _ = extract_all(typescript_extractor, EXPRESS, "routes.ts")
    health = next(e for e in endpoints if e.path == "/api/health")

    assert health.parameters == []


def test_decorator_run_is_not_attributed_to_later_methods(typescript_extractor):
    """A method with no decorators must not inherit the previous method's route."""
    source = """
@Controller("api/x")
export class XController {
  @Get("a")
  first() {}

  helper() {}
}
"""
    endpoints, _, _ = extract_all(typescript_extractor, source, "x.controller.ts")

    assert [e.handler_name for e in endpoints] == ["first"]


def test_file_without_routes_yields_no_endpoints(typescript_extractor):
    endpoints, _, _ = extract_all(typescript_extractor, "export const VALUE = 42;\n", "consts.ts")
    assert endpoints == []
