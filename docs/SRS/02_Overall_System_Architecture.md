# 02 - Overall System Architecture

## Architectural Overview
Auto Deployer follows a layered architecture composed of a React frontend, FastAPI backend,
PostgreSQL database, deployment worker and remote infrastructure.

## Main Components
- React Frontend
- FastAPI Backend
- JWT Authentication
- PostgreSQL
- Deployment Worker
- GitHub / Azure DevOps
- Linux Docker Server (MVP)

## Deployment Flow
1. Authenticate
2. Clone repository
3. Detect project
4. Generate Dockerfile (if required)
5. Build image
6. SSH connection
7. Install Docker if required
8. Run container
9. Health check
10. Store deployment logs and version
