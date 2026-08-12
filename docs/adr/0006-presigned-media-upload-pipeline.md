# Upload media directly through presigned URLs

Authorized frontend clients upload media directly to private S3-compatible quarantine storage using short-lived presigned POST or PUT credentials. Background processing validates type and size, scans malware, removes sensitive metadata, and creates optimized derivatives before an asset becomes publishable; Django controls authorization and metadata without proxying large file bodies.
