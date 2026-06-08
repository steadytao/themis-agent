# Private metrics endpoint certificate rotation

Service: internal metrics API
Environment: production

The platform team will rotate the TLS certificate used by the private metrics endpoint behind an internal Azure Application Gateway. The endpoint remains private and keeps the existing network security group rules.

Owner approval is recorded in the change ticket. The certificate chain has been validated in staging. Health check verification and monitoring checks are included. The rollback plan is to restore the previous certificate version and confirm the existing health probe is green.

Deployment window: maintenance window.
