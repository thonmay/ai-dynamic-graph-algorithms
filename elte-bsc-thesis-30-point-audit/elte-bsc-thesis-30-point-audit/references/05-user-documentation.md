# User documentation

Supervisor guidance checked 2026-09-10 sets a minimum 20-page target for user documentation. Treat that as a gate signal; evaluate usefulness and truth against the product and code.

## C3.1 Purpose, audience, and requirements

Require:

- concise task/purpose and achieved scope;
- identifiable target audiences, roles, usage context, and permission boundaries;
- minimum and optimal hardware/software requirements;
- prerequisites, dependencies, accounts, devices, services, network access, permissions, data, and costs;
- supported/unsupported platforms and known operational constraints.

Cross-check versions and prerequisites against manifests, configuration, and code. A generic “modern computer” statement is insufficient where concrete requirements exist.

## C3.2 Installation, setup, and start

Require a complete path from a clean supported environment to first successful use:

- installation and dependency versions;
- configuration files, environment variables, secrets handling, data initialization/migrations, permissions, and service startup order;
- first-launch or smoke-test confirmation;
- screenshots or command/output evidence where helpful;
- uninstall/reset/recovery information when operationally important.

Compare every command and step with repository files. If safe and feasible, rehearse it in an isolated clean environment. Do not use real production credentials. A path that only works on the student's already-configured machine is not a sufficient installation guide.

## C3.3 User processes and roles

Map every promised complex feature and major user-facing requirement to a complete workflow. Group functions by real user role/level. Each workflow should state starting state, numbered actions, expected visible result, errors/alternatives, and annotated visual evidence where the interface benefits from it.

Verify screenshots match the final software version, labels, routes, roles, and data. For CLI/API/headless systems, use equivalent request/response, command, or integration examples rather than forcing GUI screenshots.

## C3.4 Messages, troubleshooting, security, and operations

Inventory important information, warning, validation, and error messages from code/resources and compare them with the manual. Require:

- explanation and user action for important runtime messages;
- troubleshooting for realistic setup/runtime failures and known issues;
- backup, restore, reset, interruption, recovery, and log-location guidance where applicable;
- security-sensitive actions: credentials, permissions, privacy, data deletion/export, session/logout, and safe defaults;
- explicit limitations and workarounds.

Do not require every literal log message, but require complete coverage of user-actionable and safety-relevant conditions.

## Evidence output

For each point, cite thesis section/page plus corroborating file, route, configuration key, UI screen, or demo step. List any promised feature with no corresponding user workflow as a traceability defect.
