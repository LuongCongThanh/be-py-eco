# Use OpenSearch for product discovery

Product discovery requires multilingual full-text search, autocomplete, typo tolerance, synonyms, faceted filtering, sorting, popularity, and availability. PostgreSQL remains the source of truth, while OpenSearch holds a rebuildable search projection synchronized asynchronously; this accepts eventual consistency and additional operations in exchange for search behavior that would be costly to reproduce in the transactional database.
