# Keep the API and frontends in one repository

**Status: Superseded by ADR-0007.**

The Django API, customer storefront, dedicated administration frontend, and generated API client live in one repository. This keeps OpenAPI contract changes, typed client generation, and coordinated releases reviewable in one change while each application remains independently buildable and deployable.
