# Public admin service exposure

Service: internal admin portal
Environment: production

A team wants to expose an internal admin service through a public Azure Application Gateway. TLS will terminate at the edge. Network security group rules will allow any source while testing. Authentication will be added later.

The deployment is planned during business hours so the team can watch logs. The proposal does not list owner approval, approved source ranges, monitoring changes, alert checks or post-change negative-access testing.

Rollback is described as "switch it back if needed" without naming the previous listener, target, owner or verification step.
