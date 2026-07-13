# 05 - API Specification
## 5.1 Purpose

This document defines the implemented and planned REST API contract for the Auto Deployer MVP. The contract is versioned independently from the source code and must remain aligned with the generated OpenAPI/Swagger document.
## 5.2 General Conventions

- Base URL (development): `http://127.0.0.1:8000`
- Content type: `application/json`, except OAuth2 login form data.
- Authentication: `Authorization: Bearer <JWT>`
- Identifiers: UUID strings for domain resources.
- Timestamps: UTC ISO 8601.
- Unknown or foreign-owned tenant resources normally return `404 Not Found` to avoid existence disclosure.
- Long-running deployments return `202 Accepted` and execute through a worker.
- Secrets are accepted only where required and are never returned.
- Validation errors use FastAPI/Pydantic `422 Unprocessable Entity` responses.
## 5.3 Endpoint Summary

| ID | Method | URL | Status | Authentication |
|---|---|---|---|---|
| API-AUTH-001 | `POST` | `/auth/register` | Implemented | No |
| API-AUTH-002 | `POST` | `/auth/login` | Implemented | No |
| API-AUTH-003 | `GET` | `/auth/me` | Implemented | Bearer JWT required |
| API-PROJ-001 | `POST` | `/projects` | Implemented | Bearer JWT required |
| API-PROJ-002 | `GET` | `/projects` | Implemented | Bearer JWT required |
| API-PROJ-003 | `GET` | `/projects/{project_id}` | Implemented | Bearer JWT required |
| API-PROJ-004 | `PUT` | `/projects/{project_id}` | Implemented | Bearer JWT required |
| API-PROJ-005 | `DELETE` | `/projects/{project_id}` | Implemented | Bearer JWT required |
| API-ENV-001 | `POST` | `/projects/{project_id}/environments` | Planned | Bearer JWT required |
| API-ENV-002 | `GET` | `/projects/{project_id}/environments` | Planned | Bearer JWT required |
| API-ENV-003 | `POST` | `/environments/{environment_id}/test-connection` | Planned | Bearer JWT required |
| API-DEP-001 | `POST` | `/deployments` | Planned | Bearer JWT required |
| API-DEP-002 | `GET` | `/deployments` | Planned | Bearer JWT required |
| API-DEP-003 | `GET` | `/deployments/{deployment_id}` | Planned | Bearer JWT required |
| API-DEP-004 | `GET` | `/deployments/{deployment_id}/logs` | Planned | Bearer JWT required |
| API-DEP-005 | `POST` | `/deployments/{deployment_id}/rollback` | Planned | Bearer JWT required |

## API-AUTH-001 - Register User

- **Method:** `POST`
- **URL:** `/auth/register`
- **Implementation:** Implemented
- **Authentication:** No
- **Purpose:** Creates a new platform user account.
- **Authorization / isolation:** Public endpoint. The password is never returned. Password storage uses Argon2 hashing.

### Request fields

- `username`: string, 3-50 characters
- `email`: valid email address
- `password`: string, 8-128 characters

### Response model

- `id`: UUID
- `username`: string
- `email`: email
- `is_active`: boolean
- `created_at`: UTC timestamp
- `updated_at`: UTC timestamp

### Status codes

- 201 Created - user created
- 409 Conflict - username or email already exists
- 422 Unprocessable Entity - validation error
- 500 Internal Server Error - unexpected server failure

### Request example

```text
{
  "username": "selim",
  "email": "selim@example.com",
  "password": "TestPassword123!"
}
```

### Response example

```json
{
  "id": "0b06d824-5f7c-4702-9dd7-cf402bdd60de",
  "username": "selim",
  "email": "selim@example.com",
  "is_active": true,
  "created_at": "2026-07-13T12:00:00Z",
  "updated_at": "2026-07-13T12:00:00Z"
}
```

### Error scenarios

- Duplicate username/email returns 409 without revealing which other account owns it.
- Weak or malformed input returns field-level validation details.

## API-AUTH-002 - Login

- **Method:** `POST`
- **URL:** `/auth/login`
- **Implementation:** Implemented
- **Authentication:** No
- **Purpose:** Authenticates a user and returns a JWT access token.
- **Authorization / isolation:** Public endpoint. Invalid email and invalid password return the same generic response.

### Request fields

- `username`: OAuth2 form field containing the user email
- `password`: OAuth2 form field containing the plaintext password

### Response model

- `access_token`: JWT string
- `token_type`: bearer

### Status codes

- 200 OK - authentication successful
- 401 Unauthorized - invalid credentials or inactive account
- 422 Unprocessable Entity - malformed form data

### Request example

```text
Content-Type: application/x-www-form-urlencoded

username=selim@example.com&password=TestPassword123!
```

### Response example

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Error scenarios

- Invalid credentials return 401 with WWW-Authenticate: Bearer.
- Inactive users cannot receive a token.

## API-AUTH-003 - Get Current User

- **Method:** `GET`
- **URL:** `/auth/me`
- **Implementation:** Implemented
- **Authentication:** Bearer JWT required
- **Purpose:** Returns the authenticated user profile.
- **Authorization / isolation:** The user identity is taken only from the validated JWT subject claim. A caller cannot request another user by identifier.

### Request fields

- No request body.

### Response model

- `id`: UUID
- `username`: string
- `email`: email
- `is_active`: boolean
- `created_at`: UTC timestamp
- `updated_at`: UTC timestamp

### Status codes

- 200 OK - profile returned
- 401 Unauthorized - token absent, expired or invalid

### Request example

```text
Authorization: Bearer <access_token>
```

### Response example

```json
{
  "id": "0b06d824-5f7c-4702-9dd7-cf402bdd60de",
  "username": "selim",
  "email": "selim@example.com",
  "is_active": true,
  "created_at": "2026-07-13T12:00:00Z",
  "updated_at": "2026-07-13T12:00:00Z"
}
```

### Error scenarios

- Expired, malformed or revoked tokens return 401.

## API-PROJ-001 - Create Project

- **Method:** `POST`
- **URL:** `/projects`
- **Implementation:** Implemented
- **Authentication:** Bearer JWT required
- **Purpose:** Creates a deployment project owned by the authenticated user.
- **Authorization / isolation:** owner_id is always assigned from the authenticated JWT identity and is never accepted from the request body.

### Request fields

- `name`: string, 2-150 characters
- `description`: optional string, max 2000
- `repository_provider`: github | azure_devops
- `repository_url`: valid URL
- `branch`: string, default main

### Response model

- `id`: UUID
- `owner_id`: UUID
- `name`: string
- `description`: string or null
- `repository_provider`: string
- `repository_url`: string
- `branch`: string
- `created_at`: UTC timestamp
- `updated_at`: UTC timestamp

### Status codes

- 201 Created
- 401 Unauthorized
- 422 Unprocessable Entity

### Request example

```text
{
  "name": "Auto Deployer",
  "description": "Deployment automation platform",
  "repository_provider": "github",
  "repository_url": "https://github.com/selimeskimumcu/auto-deployer",
  "branch": "main"
}
```

### Response example

```json
{
  "id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
  "owner_id": "0b06d824-5f7c-4702-9dd7-cf402bdd60de",
  "name": "Auto Deployer",
  "description": "Deployment automation platform",
  "repository_provider": "github",
  "repository_url": "https://github.com/selimeskimumcu/auto-deployer",
  "branch": "main",
  "created_at": "2026-07-13T12:10:00Z",
  "updated_at": "2026-07-13T12:10:00Z"
}
```

### Error scenarios

- Unsupported provider or invalid URL returns 422.

## API-PROJ-002 - List Projects

- **Method:** `GET`
- **URL:** `/projects`
- **Implementation:** Implemented
- **Authentication:** Bearer JWT required
- **Purpose:** Lists projects owned by the authenticated user.
- **Authorization / isolation:** The database query filters by owner_id = current_user.id. No cross-user records are returned.

### Request fields

- No request body.

### Response model

- `items`: array of ProjectResponse objects; currently returned directly as an array

### Status codes

- 200 OK
- 401 Unauthorized

### Request example

```text
Authorization: Bearer <access_token>
```

### Response example

```json
[
  {
    "id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
    "owner_id": "0b06d824-5f7c-4702-9dd7-cf402bdd60de",
    "name": "Auto Deployer",
    "repository_provider": "github",
    "repository_url": "https://github.com/selimeskimumcu/auto-deployer",
    "branch": "main",
    "description": null,
    "created_at": "2026-07-13T12:10:00Z",
    "updated_at": "2026-07-13T12:10:00Z"
  }
]
```

### Error scenarios

- Invalid or missing token returns 401.

## API-PROJ-003 - Get Project

- **Method:** `GET`
- **URL:** `/projects/{project_id}`
- **Implementation:** Implemented
- **Authentication:** Bearer JWT required
- **Purpose:** Returns a single project owned by the authenticated user.
- **Authorization / isolation:** Lookup uses both project_id and owner_id. A project owned by another user deliberately returns 404 instead of 403.

### Request fields

- `project_id`: UUID path parameter

### Response model

- `project`: ProjectResponse

### Status codes

- 200 OK
- 401 Unauthorized
- 404 Not Found - missing or not owned

### Request example

```text
GET /projects/7c631d2e-2dc2-4373-8d76-848e9ec42380
```

### Response example

```json
{
  "id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
  "owner_id": "0b06d824-5f7c-4702-9dd7-cf402bdd60de",
  "name": "Auto Deployer",
  "description": null,
  "repository_provider": "github",
  "repository_url": "https://github.com/selimeskimumcu/auto-deployer",
  "branch": "main",
  "created_at": "2026-07-13T12:10:00Z",
  "updated_at": "2026-07-13T12:10:00Z"
}
```

### Error scenarios

- Malformed UUID returns 422.
- Unknown or foreign-owned project returns 404.

## API-PROJ-004 - Update Project

- **Method:** `PUT`
- **URL:** `/projects/{project_id}`
- **Implementation:** Implemented
- **Authentication:** Bearer JWT required
- **Purpose:** Updates selected fields of a project owned by the authenticated user.
- **Authorization / isolation:** The project is loaded using project_id and current owner_id before mutation.

### Request fields

- `project_id`: UUID path parameter
- `body`: any subset of name, description, repository_provider, repository_url, branch

### Response model

- `project`: updated ProjectResponse

### Status codes

- 200 OK
- 401 Unauthorized
- 404 Not Found
- 422 Unprocessable Entity

### Request example

```text
{
  "name": "Auto Deployer MVP",
  "branch": "develop"
}
```

### Response example

```json
{
  "id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
  "owner_id": "0b06d824-5f7c-4702-9dd7-cf402bdd60de",
  "name": "Auto Deployer MVP",
  "description": null,
  "repository_provider": "github",
  "repository_url": "https://github.com/selimeskimumcu/auto-deployer",
  "branch": "develop",
  "created_at": "2026-07-13T12:10:00Z",
  "updated_at": "2026-07-13T12:30:00Z"
}
```

### Error scenarios

- Foreign-owned project returns 404.
- Invalid provider, URL or field length returns 422.

## API-PROJ-005 - Delete Project

- **Method:** `DELETE`
- **URL:** `/projects/{project_id}`
- **Implementation:** Implemented
- **Authentication:** Bearer JWT required
- **Purpose:** Deletes a project owned by the authenticated user.
- **Authorization / isolation:** Only the owner can delete the project. The API should later reject deletion while an active deployment is running.

### Request fields

- `project_id`: UUID path parameter

### Response model

- `body`: none

### Status codes

- 204 No Content
- 401 Unauthorized
- 404 Not Found

### Request example

```text
DELETE /projects/7c631d2e-2dc2-4373-8d76-848e9ec42380
```

### Response example

```json
HTTP 204 with an empty body.
```

### Error scenarios

- Unknown or foreign-owned project returns 404.
- Future: active deployment conflict returns 409.

## API-ENV-001 - Create Environment

- **Method:** `POST`
- **URL:** `/projects/{project_id}/environments`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Creates a target deployment environment for a project.
- **Authorization / isolation:** The parent project must belong to current_user. Secret fields are encrypted and never returned.

### Request fields

- `name`: string
- `environment_type`: linux_docker for MVP
- `host`: IP address or hostname
- `ssh_port`: integer, default 22
- `username`: server user
- `authentication`: password or private_key secret input
- `application_port`: external port
- `container_port`: container port
- `domain`: optional domain
- `is_production`: boolean

### Response model

- `environment`: EnvironmentResponse without plaintext secret

### Status codes

- 201 Created
- 401 Unauthorized
- 404 Project Not Found
- 409 Duplicate Name or Port Conflict
- 422 Validation Error

### Request example

```text
{
  "name": "Production",
  "environment_type": "linux_docker",
  "host": "203.0.113.10",
  "ssh_port": 22,
  "username": "ubuntu",
  "auth_type": "private_key",
  "private_key": "<sensitive-value>",
  "application_port": 8080,
  "container_port": 8000,
  "domain": "api.example.com",
  "is_production": true
}
```

### Response example

```json
{
  "id": "3233cb10-5bdd-4b5b-abd1-0bc63b8919ba",
  "project_id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
  "name": "Production",
  "environment_type": "linux_docker",
  "host": "203.0.113.10",
  "ssh_port": 22,
  "username": "ubuntu",
  "application_port": 8080,
  "container_port": 8000,
  "domain": "api.example.com",
  "is_production": true
}
```

### Error scenarios

- Credentials are not logged.
- Unsupported environment types return 422 in MVP.

## API-ENV-002 - List Environments

- **Method:** `GET`
- **URL:** `/projects/{project_id}/environments`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Lists environments belonging to one owned project.
- **Authorization / isolation:** Ownership is inherited from the parent project.

### Request fields

- `project_id`: UUID path parameter

### Response model

- `items`: array of EnvironmentResponse

### Status codes

- 200 OK
- 401 Unauthorized
- 404 Project Not Found

### Request example

```text
GET /projects/7c631d2e-2dc2-4373-8d76-848e9ec42380/environments
```

### Response example

```json
[
  {
    "id": "3233cb10-5bdd-4b5b-abd1-0bc63b8919ba",
    "name": "Production",
    "environment_type": "linux_docker",
    "host": "203.0.113.10",
    "ssh_port": 22,
    "application_port": 8080,
    "container_port": 8000,
    "domain": "api.example.com",
    "is_production": true
  }
]
```

### Error scenarios

- Foreign-owned project returns 404.

## API-ENV-003 - Test Environment Connection

- **Method:** `POST`
- **URL:** `/environments/{environment_id}/test-connection`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Tests SSH connectivity and inspects the target operating system and Docker state without deploying.
- **Authorization / isolation:** Environment ownership is resolved through environment.project.owner_id. Sensitive connection details are masked.

### Request fields

- `environment_id`: UUID path parameter

### Response model

- `reachable`: boolean
- `operating_system`: string
- `docker_installed`: boolean
- `docker_running`: boolean
- `sudo_available`: boolean
- `message`: safe diagnostic text

### Status codes

- 200 OK - test completed
- 401 Unauthorized
- 404 Not Found
- 422 Unsupported Server
- 502 Bad Gateway - connection failure

### Request example

```text
POST /environments/3233cb10-5bdd-4b5b-abd1-0bc63b8919ba/test-connection
```

### Response example

```json
{
  "reachable": true,
  "operating_system": "Ubuntu 24.04",
  "docker_installed": true,
  "docker_running": true,
  "sudo_available": true,
  "message": "Connection test completed successfully."
}
```

### Error scenarios

- Timeout and authentication errors return sanitized messages.

## API-DEP-001 - Start Deployment

- **Method:** `POST`
- **URL:** `/deployments`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Creates and queues a deployment job for a project environment.
- **Authorization / isolation:** Project and environment must belong to current_user and environment.project_id must match request project_id.

### Request fields

- `project_id`: UUID
- `environment_id`: UUID
- `branch`: optional override
- `commit_sha`: optional exact revision
- `environment_variables`: optional secret/non-secret key-value values

### Response model

- `id`: UUID
- `status`: queued
- `project_id`: UUID
- `environment_id`: UUID
- `version_number`: integer
- `queued_at`: UTC timestamp

### Status codes

- 202 Accepted
- 400 Invalid Configuration
- 401 Unauthorized
- 404 Project or Environment Not Found
- 409 Deployment Already Running
- 422 Validation Error

### Request example

```text
{
  "project_id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
  "environment_id": "3233cb10-5bdd-4b5b-abd1-0bc63b8919ba",
  "branch": "main"
}
```

### Response example

```json
{
  "id": "579c379b-4d74-4b73-b592-e6c203205cc2",
  "status": "queued",
  "project_id": "7c631d2e-2dc2-4373-8d76-848e9ec42380",
  "environment_id": "3233cb10-5bdd-4b5b-abd1-0bc63b8919ba",
  "version_number": 4,
  "queued_at": "2026-07-13T13:00:00Z"
}
```

### Error scenarios

- API returns immediately after queueing; deployment work is not executed inside the request.
- A production environment can enforce one active deployment at a time.

## API-DEP-002 - List Deployments

- **Method:** `GET`
- **URL:** `/deployments`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Lists deployment history visible to the authenticated user.
- **Authorization / isolation:** Query joins deployments to owned projects. User-supplied filters never bypass the owner predicate.

### Request fields

- `project_id`: optional query filter
- `environment_id`: optional query filter
- `status`: optional query filter
- `page`: positive integer
- `page_size`: 1-100

### Response model

- `items`: array of DeploymentSummary
- `page`: integer
- `page_size`: integer
- `total`: integer

### Status codes

- 200 OK
- 401 Unauthorized
- 422 Invalid Filter

### Request example

```text
GET /deployments?project_id=7c631d2e-2dc2-4373-8d76-848e9ec42380&page=1&page_size=20
```

### Response example

```json
{
  "items": [
    {
      "id": "579c379b-4d74-4b73-b592-e6c203205cc2",
      "version_number": 4,
      "status": "succeeded",
      "branch": "main",
      "commit_sha": "a84f9d2",
      "started_at": "2026-07-13T13:00:00Z",
      "completed_at": "2026-07-13T13:02:37Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### Error scenarios

- Foreign project/environment filters return an empty set or 404 according to final endpoint policy.

## API-DEP-003 - Get Deployment

- **Method:** `GET`
- **URL:** `/deployments/{deployment_id}`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Returns deployment metadata and ordered step status.
- **Authorization / isolation:** Deployment visibility is inherited from deployment.project.owner_id.

### Request fields

- `deployment_id`: UUID path parameter

### Response model

- `deployment`: DeploymentDetail including steps but excluding sensitive raw values

### Status codes

- 200 OK
- 401 Unauthorized
- 404 Not Found

### Request example

```text
GET /deployments/579c379b-4d74-4b73-b592-e6c203205cc2
```

### Response example

```json
{
  "id": "579c379b-4d74-4b73-b592-e6c203205cc2",
  "version_number": 4,
  "status": "succeeded",
  "branch": "main",
  "commit_sha": "a84f9d2",
  "steps": [
    {"order": 1, "name": "Clone repository", "status": "succeeded"},
    {"order": 2, "name": "Build image", "status": "succeeded"}
  ]
}
```

### Error scenarios

- Foreign-owned deployment returns 404.

## API-DEP-004 - Get Deployment Logs

- **Method:** `GET`
- **URL:** `/deployments/{deployment_id}/logs`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Returns paginated, sanitized deployment logs.
- **Authorization / isolation:** Deployment ownership is checked before any log query. Secrets are masked before persistence and response.

### Request fields

- `deployment_id`: UUID path parameter
- `after_id`: optional cursor
- `limit`: 1-1000
- `level`: optional log-level filter

### Response model

- `items`: log entries
- `next_cursor`: nullable cursor

### Status codes

- 200 OK
- 401 Unauthorized
- 404 Not Found
- 422 Invalid Pagination

### Request example

```text
GET /deployments/579c379b-4d74-4b73-b592-e6c203205cc2/logs?limit=100
```

### Response example

```json
{
  "items": [
    {
      "id": 1081,
      "level": "INFO",
      "message": "Docker image built successfully.",
      "created_at": "2026-07-13T13:01:10Z"
    }
  ],
  "next_cursor": null
}
```

### Error scenarios

- Logs containing secret-like values are masked.
- High-volume log retrieval requires pagination/cursor limits.

## API-DEP-005 - Rollback Deployment

- **Method:** `POST`
- **URL:** `/deployments/{deployment_id}/rollback`
- **Implementation:** Planned
- **Authentication:** Bearer JWT required
- **Purpose:** Queues a rollback using the immutable artifact/image from a previous successful deployment.
- **Authorization / isolation:** The source deployment must belong to the authenticated user through the same environment. Rollback cannot target an artifact outside the latest retained versions.

### Request fields

- `deployment_id`: UUID identifying the target historical successful deployment
- `reason`: optional string for audit history

### Response model

- `rollback_deployment_id`: UUID
- `source_deployment_id`: UUID
- `status`: queued
- `target_version_number`: integer

### Status codes

- 202 Accepted
- 400 Source Deployment Not Successful
- 401 Unauthorized
- 404 Not Found
- 409 Deployment Already Running or Artifact Missing
- 410 Gone - version pruned

### Request example

```text
{
  "reason": "Version 5 failed health checks after release."
}
```

### Response example

```json
{
  "rollback_deployment_id": "596a3028-b202-4906-84cf-b30e6ddfb1e8",
  "source_deployment_id": "579c379b-4d74-4b73-b592-e6c203205cc2",
  "status": "queued",
  "target_version_number": 4
}
```

### Error scenarios

- Database migrations are not rolled back by the MVP.
- Missing or pruned image returns 409 or 410 and leaves the active version unchanged.

## 5.4 Standard Error Model

```json
{
  "detail": "Human-readable error message."
}
```

Validation errors may return FastAPI's structured `detail` array containing field locations and messages. Production error responses must not include stack traces, SQL details, credentials or remote server secrets.
## 5.5 Authorization Matrix

| Resource | Access rule | Foreign-owned identifier result |
|---|---|---|
| Current user | JWT subject only | Not applicable |
| Project | `project.owner_id == current_user.id` | 404 |
| Environment | `environment.project.owner_id == current_user.id` | 404 |
| Deployment | `deployment.project.owner_id == current_user.id` | 404 |
| Deployment logs | Parent deployment ownership | 404 |
| Rollback | Parent deployment ownership + retained version | 404/410 |
## 5.6 API Versioning and Compatibility

The MVP initially exposes unversioned paths. Before external production use, endpoints should move under `/api/v1`. Backward-incompatible request or response changes require a new API version. Additive optional fields may be introduced without breaking the current version.
## 5.7 Pagination, Filtering and Ordering

Collection endpoints that can grow significantly use page or cursor pagination. Deployment logs use cursor pagination because logs are append-only and high-volume. Default ordering is newest first for projects/deployments and oldest first for log streaming within a selected cursor window.
## 5.8 API Acceptance Criteria

- Implemented endpoints match Swagger/OpenAPI and this document.
- Protected endpoints return 401 without a valid token.
- Cross-user resource access never returns another user's data.
- Deployment creation returns 202 and does not block until completion.
- Credentials and secrets never appear in responses or logs.
- Rollback creates a new auditable deployment record rather than mutating historical records.
- Common errors use consistent status codes and sanitized messages.
