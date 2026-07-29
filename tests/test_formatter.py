"""Tests for tech.md and YAML rendering of an ExtractionResult."""

import yaml

from speclens import (
    Endpoint,
    ExtractionResult,
    Parameter,
    ServiceMethod,
    TypeDefinition,
    format_tech_md,
    format_yaml,
)


def sample_result() -> ExtractionResult:
    return ExtractionResult(
        endpoints=[
            Endpoint(
                http_method="POST",
                path="/api/accounts",
                handler_name="createAccount",
                file_path="AccountController.java",
                line_number=15,
                parameters=[Parameter(name="request", type="CreateAccountRequest", source="body")],
                return_type="AccountResponse",
                request_body_type="CreateAccountRequest",
                auth_required=True,
                roles=["ADMIN"],
            ),
            Endpoint(
                http_method="GET",
                path="/api/accounts/{id}",
                handler_name="getAccount",
                file_path="AccountController.java",
                line_number=10,
                parameters=[Parameter(name="id", type="String", source="path")],
                return_type="AccountResponse",
            ),
        ],
        types=[
            TypeDefinition(
                name="CreateAccountRequest",
                file_path="dto.java",
                line_number=3,
                kind="class",
                fields=[
                    Parameter(name="customerId", type="String"),
                    Parameter(name="balance", type="Double", required=False),
                ],
            ),
            TypeDefinition(
                name="Account",
                file_path="entity.java",
                line_number=8,
                kind="class",
                annotations=["@Entity"],
                fields=[Parameter(name="id", type="Long")],
            ),
        ],
        service_methods=[
            ServiceMethod(
                name="getAccount",
                file_path="AccountService.java",
                line_number=4,
                parameters=[Parameter(name="id", type="String")],
                return_type="AccountResponse",
                interface_name="AccountService",
            )
        ],
    )


def test_tech_md_includes_project_name_header():
    output = format_tech_md(sample_result(), "CardDemo")

    assert output.startswith("# CardDemo — Extracted API Surface")


def test_tech_md_renders_each_endpoint_with_method_and_path():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "#### POST `/api/accounts`" in output
    assert "#### GET `/api/accounts/{id}`" in output


def test_tech_md_renders_auth_roles_and_source_location():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "**Auth**: ADMIN" in output
    assert "`AccountController.java:15`" in output


def test_tech_md_renders_parameter_table_with_source_and_requiredness():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "| request | `CreateAccountRequest` | body | yes |" in output
    assert "| id | `String` | path | yes |" in output


def test_tech_md_separates_dtos_from_entities():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "### Request/Response Types (DTOs)" in output
    assert "### Entities/Models" in output
    # An @Entity-annotated type is grouped as an entity.
    assert output.index("### Request/Response Types (DTOs)") < output.index("### Entities/Models")


def test_tech_md_marks_optional_fields():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "| balance | `Double` | no |" in output


def test_tech_md_renders_service_interface_signatures():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "### AccountService" in output
    assert "`getAccount(id: String) → AccountResponse`" in output


def test_tech_md_includes_warnings_when_errors_present():
    result = sample_result()
    result.errors.append("Broken.java: boom")

    output = format_tech_md(result, "CardDemo")

    assert "## Extraction Warnings" in output
    assert "Broken.java: boom" in output


def test_tech_md_omits_warnings_section_when_clean():
    output = format_tech_md(sample_result(), "CardDemo")

    assert "## Extraction Warnings" not in output


def test_empty_result_still_renders_a_valid_header():
    output = format_tech_md(ExtractionResult(), "Empty")

    assert "# Empty — Extracted API Surface" in output
    assert "## API Endpoints" not in output


def test_yaml_output_is_parseable_and_structured():
    data = yaml.safe_load(format_yaml(sample_result()))

    assert set(data) == {"endpoints", "types", "service_methods"}
    assert len(data["endpoints"]) == 2


def test_yaml_endpoint_carries_method_path_and_auth():
    data = yaml.safe_load(format_yaml(sample_result()))
    post = next(e for e in data["endpoints"] if e["method"] == "POST")

    assert post["path"] == "/api/accounts"
    assert post["handler"] == "createAccount"
    assert post["auth_required"] is True
    assert post["roles"] == ["ADMIN"]
    assert post["file"] == "AccountController.java:15"


def test_yaml_omits_default_param_metadata():
    """Required body params are the default, so those keys stay absent."""
    data = yaml.safe_load(format_yaml(sample_result()))
    post = next(e for e in data["endpoints"] if e["method"] == "POST")
    param = post["parameters"][0]

    assert param == {"name": "request", "type": "CreateAccountRequest"}


def test_yaml_records_non_default_param_source():
    data = yaml.safe_load(format_yaml(sample_result()))
    get = next(e for e in data["endpoints"] if e["method"] == "GET")

    assert get["parameters"][0]["source"] == "path"


def test_yaml_types_include_fields_and_kind():
    data = yaml.safe_load(format_yaml(sample_result()))
    by_name = {t["name"]: t for t in data["types"]}

    assert by_name["CreateAccountRequest"]["kind"] == "class"
    assert by_name["CreateAccountRequest"]["fields"][1]["required"] is False
