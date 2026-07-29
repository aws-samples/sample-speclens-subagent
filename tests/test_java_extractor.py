"""Tests for the Spring Boot / Java API surface extractor."""

from conftest import extract_all

CONTROLLER = """
package com.example.demo;

import org.springframework.web.bind.annotation.*;
import org.springframework.security.access.prepost.PreAuthorize;

@RestController
@RequestMapping("/api/accounts")
public class AccountController {

    @GetMapping("/{accountId}")
    public AccountResponse getAccount(@PathVariable String accountId) {
        return null;
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public AccountResponse createAccount(@RequestBody CreateAccountRequest request) {
        return null;
    }

    @GetMapping
    public AccountListResponse listAccounts(@RequestParam(required = false) Integer page) {
        return null;
    }

    @RequestMapping(value = "/{accountId}/close", method = RequestMethod.DELETE)
    public void closeAccount(@PathVariable String accountId) {
    }
}
"""


def endpoints_by_handler(endpoints):
    return {e.handler_name: e for e in endpoints}


def test_class_level_request_mapping_prefixes_method_path(java_extractor):
    """Class-level @RequestMapping must be prepended to each method path."""
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["getAccount"].path == "/api/accounts/{accountId}"


def test_bare_mapping_inherits_class_base_path(java_extractor):
    """A @PostMapping with no path argument maps to the class base path itself."""
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["createAccount"].path == "/api/accounts"
    assert by_handler["listAccounts"].path == "/api/accounts"


def test_http_methods_are_mapped_from_annotations(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["getAccount"].http_method == "GET"
    assert by_handler["createAccount"].http_method == "POST"


def test_request_mapping_method_attribute_is_honored(java_extractor):
    """@RequestMapping(method = RequestMethod.DELETE) must not default to GET."""
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["closeAccount"].http_method == "DELETE"
    assert by_handler["closeAccount"].path == "/api/accounts/{accountId}/close"


def test_parameter_sources_are_classified(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    path_param = by_handler["getAccount"].parameters[0]
    assert path_param.name == "accountId"
    assert path_param.source == "path"

    query_param = by_handler["listAccounts"].parameters[0]
    assert query_param.source == "query"


def test_request_body_type_is_captured(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["createAccount"].request_body_type == "CreateAccountRequest"


def test_method_level_preauthorize_marks_auth_and_roles(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    create = by_handler["createAccount"]
    assert create.auth_required is True
    assert "hasRole('ADMIN')" in create.roles

    assert by_handler["getAccount"].auth_required is False


def test_return_type_is_captured(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")
    by_handler = endpoints_by_handler(endpoints)

    assert by_handler["getAccount"].return_type == "AccountResponse"


def test_line_numbers_are_one_indexed(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, CONTROLLER, "AccountController.java")

    for endpoint in endpoints:
        assert endpoint.line_number >= 1
        assert endpoint.file_path == "AccountController.java"


DTO = """
package com.example.demo;

import jakarta.persistence.Entity;

public class CreateAccountRequest {
    private String customerId;
    private Double initialBalance;
}

@Entity
public class Account {
    private Long id;
    private String status;
}
"""


def test_dto_fields_are_extracted_with_types(java_extractor):
    _, types, _ = extract_all(java_extractor, DTO, "dto.java")
    by_name = {t.name: t for t in types}

    request = by_name["CreateAccountRequest"]
    fields = {f.name: f.type for f in request.fields}
    assert fields == {"customerId": "String", "initialBalance": "Double"}


def test_entity_annotation_is_recorded(java_extractor):
    _, types, _ = extract_all(java_extractor, DTO, "dto.java")
    by_name = {t.name: t for t in types}

    assert any("Entity" in a for a in by_name["Account"].annotations)


SERVICE = """
package com.example.demo;

public interface AccountService {
    AccountResponse getAccount(String accountId);
    void closeAccount(String accountId, String reason);
}
"""


def test_service_interface_methods_are_extracted(java_extractor):
    _, _, methods = extract_all(java_extractor, SERVICE, "AccountService.java")
    by_name = {m.name: m for m in methods}

    assert "getAccount" in by_name
    assert by_name["getAccount"].return_type == "AccountResponse"
    assert by_name["getAccount"].interface_name == "AccountService"

    close = by_name["closeAccount"]
    assert [p.name for p in close.parameters] == ["accountId", "reason"]


def test_class_without_routes_yields_no_endpoints(java_extractor):
    endpoints, _, _ = extract_all(java_extractor, DTO, "dto.java")
    assert endpoints == []
