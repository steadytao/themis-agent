# Context network policy

Public endpoints must not use 0.0.0.0/0 or unrestricted source ranges for administrative surfaces without a named exception. Approved CIDR ranges, WAF policy and negative-access tests should be recorded before deployment.

Network security group changes should be reviewed for blast radius, logging and least privilege. Changes that increase public reachability require stronger verification than private-only changes.
