"""Tests for the Gin / Chi / Echo / net-http Go API surface extractor."""

from conftest import extract_all

HANDLER = """
package main

type CreateAccountRequest struct {
	CustomerID     string  `json:"customerId"`
	InitialBalance float64 `json:"initialBalance,omitempty"`
}

type AccountService interface {
	GetAccount(id string) (*Account, error)
	CloseAccount(id string, reason string) error
}

func RegisterRoutes(r *gin.Engine) {
	r.GET("/api/accounts/:id", getAccount)
	r.POST("/api/accounts", createAccount)
	r.DELETE("/api/accounts/:id", deleteAccount)
}
"""


def test_gin_routes_are_extracted_with_methods_and_paths(go_extractor):
    endpoints, _, _ = extract_all(go_extractor, HANDLER, "handler.go")

    routes = {(e.http_method, e.path) for e in endpoints}
    assert ("GET", "/api/accounts/:id") in routes
    assert ("POST", "/api/accounts") in routes
    assert ("DELETE", "/api/accounts/:id") in routes


def test_route_handler_names_are_captured(go_extractor):
    endpoints, _, _ = extract_all(go_extractor, HANDLER, "handler.go")
    handlers = {e.handler_name for e in endpoints}

    assert {"getAccount", "createAccount", "deleteAccount"} <= handlers


def test_struct_fields_are_extracted_with_go_types(go_extractor):
    _, types, _ = extract_all(go_extractor, HANDLER, "handler.go")
    by_name = {t.name: t for t in types}

    request = by_name["CreateAccountRequest"]
    assert request.kind == "struct"

    fields = {f.name: f.type for f in request.fields}
    assert fields == {"CustomerID": "string", "InitialBalance": "float64"}


def test_omitempty_json_tag_marks_field_optional(go_extractor):
    _, types, _ = extract_all(go_extractor, HANDLER, "handler.go")
    by_name = {t.name: t for t in types}

    fields = {f.name: f.required for f in by_name["CreateAccountRequest"].fields}
    assert fields["CustomerID"] is True
    assert fields["InitialBalance"] is False


def test_interface_methods_are_extracted(go_extractor):
    """The current grammar emits `method_elem` rather than `method_spec`."""
    _, _, methods = extract_all(go_extractor, HANDLER, "handler.go")
    by_name = {m.name: m for m in methods}

    assert "GetAccount" in by_name
    assert by_name["GetAccount"].interface_name == "AccountService"


def test_interface_method_params_are_not_overwritten_by_return_types(go_extractor):
    """The first parameter_list is arguments; the second is return types."""
    _, _, methods = extract_all(go_extractor, HANDLER, "handler.go")
    by_name = {m.name: m for m in methods}

    close = by_name["CloseAccount"]
    assert [p.name for p in close.parameters] == ["id", "reason"]
    assert close.return_type == "error"


def test_multi_value_return_is_captured(go_extractor):
    _, _, methods = extract_all(go_extractor, HANDLER, "handler.go")
    by_name = {m.name: m for m in methods}

    assert by_name["GetAccount"].return_type == "(*Account, error)"


NET_HTTP = """
package main

func main() {
	http.HandleFunc("/api/health", healthHandler)
}
"""


def test_net_http_handlefunc_is_extracted(go_extractor):
    endpoints, _, _ = extract_all(go_extractor, NET_HTTP, "server.go")

    assert any(e.path == "/api/health" for e in endpoints)


def test_file_without_routes_yields_no_endpoints(go_extractor):
    endpoints, _, _ = extract_all(
        go_extractor, "package main\n\nfunc add(a int, b int) int { return a + b }\n", "math.go"
    )
    assert endpoints == []
