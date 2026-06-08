# Context architecture note

Administrative services are normally reachable only through private network paths. Public exposure requires documented service-owner approval, explicit identity controls and a reason why the service cannot remain private.

Azure Application Gateway and load balancer changes must record the listener, target, certificate, source ranges and health probe being changed. Reviewers should be able to identify the previous known-good route before the change begins.
