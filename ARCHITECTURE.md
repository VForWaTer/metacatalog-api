# Metacatalog API System Architecture

## Overview

The Metacatalog API is a FastAPI-based metadata management system with a SvelteKit frontend application (Manager) integrated as a sub-application. The system provides RESTful APIs for managing metadata entries, authors, licenses, and related data.

## Architecture Components

### 1. Backend Server (`metacatalog_api/server.py`)

- **Base FastAPI Application**: Core server with lifespan management
- **Database Initialization**: Automatically checks and installs database schema on startup
- **Version Management**: Validates database version and supports auto-upgrade
- **Admin Token Setup**: Handles development mode admin token creation
- **Configuration**: Uses Pydantic Settings with CLI support and environment variable prefix `METACATALOG_`

### 2. Application Entry Point (`metacatalog_api/default_server.py`)

The main application server that:
- Mounts the Manager SvelteKit app as static files at `/manager`
- Includes all API routers (read, create, upload, data, preview, export, security)
- Sets up CORS middleware for cross-origin requests
- Redirects root path (`/`) to `/manager`
- Applies API key authentication to write operations (create, upload, data, preview)

### 3. Manager Application (`metacatalog_api/apps/manager/`)

A **SvelteKit** frontend application that provides a web UI for managing metadata:

#### Frontend Architecture
- **Framework**: SvelteKit 5 with TypeScript
- **Styling**: Tailwind CSS 4
- **Build**: Vite with static adapter (`@sveltejs/adapter-static`)
- **SSR**: Disabled (client-side only)
- **Routes**:
  - `/manager` - Main dashboard
  - `/manager/list` - Browse/search entries
  - `/manager/new` - Create new metadata entry
  - `/manager/datasets/[id]` - View/edit individual dataset
  - `/manager/extend` - Extend functionality

#### API Integration
- **API Communication**: Uses `fetch` API with custom `devFetch` wrapper
- **Backend URL**: Configurable via `VITE_BACKEND_URL` environment variable (defaults to `http://localhost:8001`)
- **Authentication**: API key-based via `X-API-Key` header
- **API Endpoints Used**:
  - `GET /entries` - List/search entries
  - `POST /entries` - Create new entry
  - `GET /entries/{id}` - Get specific entry
  - `POST /uploads` - Upload data files
  - `POST /entries/{entry_id}/datasource` - Add datasource to entry
  - Various lookup endpoints (authors, licenses, variables, keywords)

#### State Management
- **Svelte Stores**: Used for application state
  - `settingsStore`: Backend URL configuration and dev logging
  - `metadataStore`: Form state and validation
  - `apiKeyStore`: API key management and validation

### 4. API Routers (`metacatalog_api/router/api/`)

#### Read Router (`read.py`)
- **Public Endpoints** (no authentication required):
  - `GET /entries` - List/search entries with filtering
  - `GET /entries/{id}` - Get specific entry
  - `GET /locations.json` - Get GeoJSON locations
  - `GET /licenses` - List licenses
  - `GET /authors` - List/search authors
  - `GET /variables` - List variables
  - `GET /keywords` - List keywords
  - `GET /groups` - List entry groups

#### Create Router (`create.py`)
- **Protected Endpoints** (requires API key):
  - `POST /entries` - Create new metadata entry
  - `POST /entries/{entry_id}/datasource` - Add datasource
  - `POST /authors` - Create author
  - `POST /groups` - Create entry group

#### Upload Router (`upload.py`)
- **Protected Endpoints**:
  - `POST /uploads` - Upload files (returns file hash for later use)

#### Security Router (`security.py`)
- `GET /validate` - Validate API key
- `validate_api_key` dependency used by protected routes

### 5. Core Business Logic (`metacatalog_api/core.py`)

Provides high-level functions that:
- Manage database connections via context managers
- Implement business logic for CRUD operations
- Handle file uploads via `UploadCache`
- Support database migrations
- Token registration and management

### 6. Database Layer (`metacatalog_api/db.py`)

- **ORM**: SQLModel (SQLAlchemy-based)
- **Database**: PostgreSQL
- **Connection**: Managed via `core.connect()` context manager
- **Versioning**: Database schema versioning system
- **Migrations**: SQL-based migration files in `metacatalog_api/sql/migrate/`

## Request Flow

### Read Operations (Public)
```
Browser → Manager App → FastAPI → Read Router → Core → Database → Response
```

### Write Operations (Authenticated)
```
Browser → Manager App → FastAPI → Security Middleware → Create/Upload Router → Core → Database → Response
```

## Authentication Flow

1. Manager app stores API key in `apiKeyStore`
2. For write operations, includes `X-API-Key` header
3. FastAPI `validate_api_key` dependency checks token against database
4. If valid, request proceeds; if invalid, returns 401

## Development vs Production

### Development
- Manager app runs via Vite dev server (typically on different port)
- Frontend makes API calls to backend URL (configurable)
- Development logging enabled in frontend
- Admin token auto-created in development mode

### Production
- Manager app built to static files (`dist/` directory)
- Static files served by FastAPI at `/manager` route
- Same-origin requests (no CORS issues)
- API key must be manually configured

## Key Design Patterns

1. **Separation of Concerns**: Frontend (SvelteKit) and backend (FastAPI) are separate applications
2. **API-First**: All functionality exposed via REST API
3. **Authentication**: API key-based for write operations, public read access
4. **Static Serving**: Production manager app served as static files from FastAPI
5. **Database Abstraction**: Core module provides high-level database operations
6. **Version Management**: Database schema versioning with migration support

