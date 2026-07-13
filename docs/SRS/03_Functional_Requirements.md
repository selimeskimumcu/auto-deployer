# 03 - Functional Requirements

## FR-001 - User Registration
**Priority:** Must

**Description:** Users can create an account using username, email and password.

**Acceptance Criteria:** New user is stored securely with hashed password.

## FR-002 - User Authentication
**Priority:** Must

**Description:** Users authenticate using JWT tokens.

**Acceptance Criteria:** Valid credentials return an access token.

## FR-003 - Project Management
**Priority:** Must

**Description:** Users can create, edit, list and delete projects.

**Acceptance Criteria:** Only project owner can manage the project.

## FR-004 - Repository Registration
**Priority:** Must

**Description:** Users register GitHub or Azure DevOps repositories.

**Acceptance Criteria:** Repository URL and branch are validated and stored.

## FR-005 - Environment Management
**Priority:** Must

**Description:** Users define Linux deployment environments.

**Acceptance Criteria:** Environment is linked to the authenticated user.

## FR-006 - Repository Clone
**Priority:** Must

**Description:** The system clones the configured repository before deployment.

**Acceptance Criteria:** Repository is cloned successfully into a workspace.

## FR-007 - Docker Detection
**Priority:** Must

**Description:** Platform detects whether a Dockerfile exists.

**Acceptance Criteria:** Existing Dockerfile is used or a new one is generated.

## FR-008 - Docker Installation
**Priority:** Must

**Description:** Target server is checked for Docker installation.

**Acceptance Criteria:** Docker is installed automatically when missing.

## FR-009 - Application Deployment
**Priority:** Must

**Description:** Application is deployed to the target Linux server.

**Acceptance Criteria:** Container starts successfully and health check passes.

## FR-010 - Deployment Logging
**Priority:** Should

**Description:** Deployment logs and status are stored.

**Acceptance Criteria:** User can view deployment history.

## FR-011 - Rollback
**Priority:** Must

**Description:** Users can rollback to one of the last ten successful deployments.

**Acceptance Criteria:** Selected version becomes active successfully.

## FR-012 - User Isolation
**Priority:** Must

**Description:** Users cannot access projects or environments owned by others.

**Acceptance Criteria:** Unauthorized requests return an error and no data leakage occurs.

