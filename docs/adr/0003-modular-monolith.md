# Build a modular monolith

The commerce backend is one Django deployment divided into domain-focused apps with explicit ownership and public interfaces. Modules share PostgreSQL and infrastructure but must not reach into one another's internal models or services; this keeps transactions and operations simple now while preserving seams that can become separate services only when measured scaling or organizational needs justify it.
