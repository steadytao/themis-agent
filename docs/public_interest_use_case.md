# Public-interest use case

Themis can help public-interest organisations review infrastructure changes before deployment.

A small school, clinic, council team or nonprofit may not have a dedicated platform-security reviewer. Themis provides a read-only way to turn a proposed change into practical review material: risks, missing evidence, verification steps, rollback questions and human-review notes.

# Example community need

A small community clinic wants remote staff to access an internal appointment-admin portal. The proposed change exposes the portal through a public edge route before authentication, source ranges, owner approval, monitoring checks and rollback evidence are fully recorded.

Themis can help the reviewer ask concrete questions before the change affects staff or patients:
- What source ranges are approved?
- Which identity provider and access policy protect the portal?
- Who owns the service and approved the exposure?
- How will unauthorised access be denied and logged?
- What post-change checks prove the route is limited to the intended audience?
- What exact rollback path restores the previous known-good state?

The project does not claim to solve staffing, governance or security maturity by itself. It gives reviewers a repeatable structure for asking better questions before deployment.

# Boundaries

Themis is advisory and read-only. It does not approve changes, deploy infrastructure, scan live systems or replace a human reviewer.

The included clinic scenario is synthetic. It is designed to show how the review pattern applies to public-interest infrastructure without using real patient, student, customer or employer data.
