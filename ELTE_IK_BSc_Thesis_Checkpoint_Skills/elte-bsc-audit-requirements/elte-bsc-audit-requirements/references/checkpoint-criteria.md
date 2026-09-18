# Checkpoint 2 mandatory criteria

Apply every gate. Use N/A only for genuinely inapplicable domain-specific elements.

## Expected evidence

- Current requirements specification in a supervisor-accessible Word/Teams/SharePoint or Overleaf form, or an equivalent supplied artifact.
- Approved/submitted topic proposal with exactly three headline contributions.
- Any approved scope change and the applicable semester/deadline.

## Mandatory gates

### C1 Purpose, scope, actors, and boundary

Define the system purpose, target users/actors or interacting systems, scope, exclusions, assumptions, dependencies, and terminology. The boundary must make clear what the student builds and what is an external dependency.

### C2 Traceability to the approved promise

Map each of the three approved contributions and every promised deliverable to numbered requirements and acceptance evidence. Identify approved changes. No contribution may disappear, and new major scope may not enter silently.

If the proposal is unavailable, this gate is Unverified.

### C3 Functional requirements

Use unique identifiers and precise, atomic, testable statements. Cover every major user/system capability. Separate behavior from implementation where possible and resolve contradictions or duplicates.

### C4 Detailed scenarios

Supply either:

- a use-case diagram plus narrative use cases; or
- a table of user stories using function name, short description, and Given-When-Then entries.

For each important workflow, identify actor/precondition, trigger, main flow, outcome, and relevant alternate/error/permission/boundary behavior. A diagram or one-line story without detailed explanation does not pass.

### C5 Acceptance criteria and evidence

Every complex contribution and high-priority requirement has observable acceptance criteria and names the demonstration, test, output, measurement, or artifact that will prove completion. Avoid subjective terms such as fast, intuitive, robust, or accurate without a threshold or method.

### C6 Data and business rules

Define important entities/data, validation, lifecycle, ownership, persistence expectations, and business rules at specification depth. For a system with no stored data, explain the data flow and mark persistence-only details N/A.

### C7 Interfaces and roles

Define relevant UI, CLI, API, device, file-format, service, authentication/authorization, and role boundaries. Exact low-level protocols are not required unless already part of the promise, but input/output and failure behavior must be clear.

### C8 Measurable quality requirements

State applicable non-functional requirements for performance, reliability, security/privacy, scalability, usability/accessibility, portability/compatibility, and maintainability. Omit an irrelevant category only with a reason. A claimed quality attribute must have a measurable target or evaluation method.

### C9 Core planning decisions and feasibility

Record enough technology, data, deployment, integration, and architectural assumptions to show the requirements can be implemented. Identify constraints, major risks, dependencies, and a realistic priority or release split. Do not demand the completed architecture deliverable.

### C10 Testability and internal consistency

Requirements, scenarios, acceptance criteria, data rules, and scope use consistent names and do not conflict. Each mandatory behavior can be tested without inventing missing conditions.

### C11 Reuse in final Developer Documentation

The document has stable headings/identifiers, clear figures/tables, and project-specific prose suitable for direct revision into the final Design chapter. Generic software-engineering boilerplate that does not constrain this system fails.

### C12 Supervisor access and delivery

The submitted version is dated/versioned and the supervisor has a stated access path. For Overleaf, the supervisor should be a collaborator and receive the project link through Teams. For Word, use Teams/SharePoint browser-accessible sharing. If the artifact is directly supplied for audit but sharing status is unknown, mark only this process gate Unverified.

## Later-stage warnings that do not independently fail checkpoint 2

Flag, but do not turn into current blockers:

- missing final class/architecture diagrams;
- fewer than ten final design pages;
- incomplete implementation or tests;
- incomplete final user documentation or bibliography.

They become blockers only when their absence reveals that the requirements themselves are untestable, infeasible, or generic.
