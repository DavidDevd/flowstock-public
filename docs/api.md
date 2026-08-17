# Public API surface

The implemented API is mounted under `/api/v1`.

| Area | Implemented routes |
| --- | --- |
| Platform | liveness and readiness |
| Identity | login, current session, logout, password change and recovery completion |
| Users | list, create, update and initiate recovery |
| Categories | list, retrieve, create and update |
| Units | list, retrieve, create and update |
| Products | list, retrieve, create and update |
| Customers | list, retrieve, create and update |

Prometheus metrics are exposed separately at `/metrics`. Interactive API documentation is enabled outside the pilot environment. Request and response schemas are defined in the source code and generated OpenAPI document.
