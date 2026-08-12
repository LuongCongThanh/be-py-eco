# Publish asynchronous work through a transactional outbox

State changes and their resulting asynchronous work must be committed atomically in PostgreSQL. A transactional outbox records events in the same transaction, and background dispatchers deliver them idempotently to Celery consumers; external payment, email, search, shipping, and analytics calls never run inside the originating database transaction.
