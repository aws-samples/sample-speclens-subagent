endpoints:
- method: GET
  path: /api/accounts/{id}
  handler: getAccount
  file: AccountController.java:4
  parameters:
  - name: id
    type: String
    source: path
  request_body_type: null
  return_type: AccountResponse
  auth_required: true
  roles:
  - hasRole('ADMIN')
- method: POST
  path: /api/accounts
  handler: create
  file: AccountController.java:8
  parameters:
  - name: request
    type: CreateAccountRequest
  request_body_type: CreateAccountRequest
  return_type: AccountResponse
  auth_required: false
  roles: []
types:
- name: AccountController
  kind: class
  file: AccountController.java:1
  fields: []
  parent_types: []
service_methods: []
