# Insighta Labs+ — Stage 3 Backend System (an improvement of stage 2)

## Overview

Insighta Labs+ extends the Stage 2 Profile Intelligence System into a production-ready platform with secure authentication, role-based access control, and multi-interface support (CLI and Web).

This system enables authenticated users to query, filter, export, and analyze profile data while enforcing strict security, consistency, and access policies.

Stage 2 features (filtering, sorting, pagination, and natural language search) remain intact and fully backward compatible.

---

## System Architecture

The system follows a **single-backend, multi-client architecture**:

```
                ┌──────────────┐
                │   Web App    │
                │ (Cookies)    │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │   Backend    │
                │ Django + DRF │
                │              │
                │ Auth Server  │
                │ + API Server │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │     CLI      │
                │ (Bearer JWT) │
                └──────────────┘
```

### Key Responsibilities of Backend:
- OAuth authentication (GitHub with PKCE)
- Token issuance and validation
- Role-based access control (RBAC)
- Profile data access and filtering
- CSV export
- Rate limiting and logging

---

## Authentication Flow

### GitHub OAuth with PKCE

The system implements the **Authorization Code Flow with PKCE** for both CLI and Web clients.

### Flow Summary:

1. Client generates:
   - `code_verifier`
   - `code_challenge = SHA256(code_verifier)`

2. User is redirected to GitHub OAuth consent page

3. GitHub returns `authorization_code`

4. Backend:
   - Exchanges `code + code_verifier` for GitHub access token
   - Fetches user profile
   - Creates or retrieves local user

5. Backend issues:
   - Access Token (short-lived)
   - Refresh Token (long-lived)

---

### CLI Authentication

- Opens browser for OAuth login
- Receives callback or manual code input
- Stores credentials locally:

```
~/.insighta/credentials.json
```

---

### Web Authentication

- Uses HTTP-only cookies for refresh tokens
- Access tokens handled server-side or short-lived in memory
- CSRF protection enforced

---

## Token Handling Strategy

### Token Types

| Token Type    | Lifetime       | Usage                     |
|--------------|---------------|---------------------------|
| Access Token | 5–15 minutes  | API authentication        |
| Refresh Token| Longer-lived  | Obtain new access tokens  |

---

### Security Features

- Refresh token rotation enabled
- Token blacklisting enabled
- Each token has a unique `JTI` (JWT ID)
- Reuse of refresh tokens is invalidated

---

### Refresh Flow

1. Client sends refresh token
2. Backend:
   - Verifies token
   - Issues new access + refresh token
   - Blacklists old refresh token

---

## Role-Based Access Control (RBAC)

### Roles

- **Admin**
  - Full access to all endpoints
- **Analyst**
  - Restricted access (read-only or scoped data)

---

### Enforcement

- Applied at **view level and endpoint level**
- Never delegated to frontend

Example permission logic:

```
Admin → Full CRUD
Analyst → Read-only / filtered visibility
```

---

## API Versioning

The API uses **URL versioning**:

```
/api/v1/
/api/v2/
```

- **v1**: Preserves Stage 2 behavior
- **v2**: Introduces updated structures and improvements

---

## Pagination

Standardized response format:

```json
{
  "count": 120,
  "next": "url",
  "previous": "url",
  "results": [...]
}
```

- Consistent across all endpoints
- Works with filtering and search

---

## CSV Export

### Endpoint

```
GET /api/v1/profiles/export?format=csv
```

### Features

- Supports filtering and search parameters
- Enforced RBAC (only authorized roles)
- Returns downloadable CSV file

---

## CLI Usage

### Installation

```
pip install insighta-cli
```

### Commands

```
insighta login
insighta list-profiles
insighta export --csv
```

---

### CLI Behavior

- Stores credentials locally
- Automatically refreshes tokens
- Attaches Authorization headers to requests

---

## Web Portal

### Security Features

- HTTP-only cookies for refresh tokens
- CSRF protection enabled
- Secure cookie settings:
  - `HttpOnly`
  - `Secure`
  - `SameSite`

---

### Responsibilities

- User login/logout
- Profile browsing and filtering
- CSV export
- Role-based UI rendering (non-authoritative)

---

## Rate Limiting

Implemented using DRF throttling.

### Example Policy

```
Authenticated users: 100 requests/minute
Anonymous users: lower threshold
```

---

## Request Logging

Each request logs:

- User ID
- Endpoint accessed
- HTTP method
- Status code
- Timestamp

### Exclusions

- Tokens are never logged
- Sensitive payload data is excluded

---

## Natural Language Parsing Approach

The system retains Stage 2 natural language search capability.

### Approach

- Input query parsed into structured filters
- Keywords mapped to model fields
- Combined with existing filtering logic

Example:

```
"engineers in Lagos with Python experience"
→ location=Lagos, role=engineer, skill=Python
```

---

## Edge Case Handling

The system accounts for:

- Expired access tokens
- Invalid or reused refresh tokens
- Unauthorized role access
- Partial OAuth flows (user cancels login)
- Empty or malformed queries
- Pagination + filtering inconsistencies
- CLI stale credential recovery

---

## Repositories

### Backend
- Django + DRF API
- Auth, RBAC, data processing

### CLI
- Python-based tool
- OAuth login + API interaction

### Web Portal
- Frontend interface
- Cookie-based authentication

---

## Deployment

### Backend URL
```
<your-backend-url>
```

### Web Portal URL
```
<your-web-url>
```

---

## Evaluation Focus

This implementation prioritizes:

- Strong security practices
- Consistent API behavior
- Clear separation of concerns
- Robust error handling
- Maintainability and extensibility

---

## Final Notes

- Stage 2 functionality is fully preserved
- All new features are layered without breaking existing behavior
- Security and correctness are treated as first-class concerns
