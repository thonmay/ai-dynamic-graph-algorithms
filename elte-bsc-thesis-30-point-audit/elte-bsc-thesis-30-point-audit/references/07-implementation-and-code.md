# Realization and code audit

Supervisor guidance checked 2026-09-10 sets a minimum 10-page implementation chapter and expects technical treatment of basic functionality and every complex feature, important code snippets, explicit design links, shortcomings, repository/version-control practice, debugging, maintenance, coding standards, static checks, and reproducible dependency/environment manifests.

## Establish the ownership boundary

Inventory languages, manifests, packages, generated code, vendored code, copied/tutorial code, assets, migrations, tests, build files, and binaries. Where history exists, inspect authorship and development trajectory without treating commit count as quality. Estimate meaningful student-authored code only after excluding generated, scaffolded, vendored, dependency, test-fixture, and machine-produced material.

Cross-check the AI declaration and point-of-use disclosures against substantial generated blocks that can be objectively identified from comments/history or supplied records. Do not use an AI detector or style speculation to assign authorship.

## C5.1 Documented implementation decisions

Require project-specific decisions about data representation, components, interfaces, language/tool features, physical/component plan, environment, and installation/deployment. The chapter should explain why important decisions were made and where they appear in code. It should include enough selected snippets to support the account, not dump the complete source.

## C5.2 Plan fidelity and technical choices

Build a design-to-code map for components, data structures, interfaces, patterns, and complex features. Verify the implementation matches the final approved design or that deviations are explicitly explained and justified. Inspect whether modern/effective language and tool mechanisms are used consciously rather than producing needless complexity.

An unimplemented proposal promise is direct evidence against fidelity even without running the program. Record the missing path in proposal, design, code, and tests.

## C5.3 Maintainability, structure, and reuse

Inspect representative and high-risk student-authored code across every major component:

- responsibilities, cohesion, coupling, dependency direction, modularity, and duplication;
- identifiers, formatting, complexity, dead code, magic values, comments, and self-documentation;
- functions, modules, interfaces, inheritance/composition, generics/templates, higher-order abstractions, or paradigm-appropriate reuse;
- configuration separation, dependency injection, testability, and maintainability;
- static-analysis/lint/type-check results and whether suppressions are justified.

Do not award from a small “best code” sample. Use broad automated inventory plus targeted deep inspection of contribution paths, integration boundaries, data access, concurrency/security code, and complex/high-churn modules.

## C5.4 Control, errors, resources, and limitations

Trace validation, exceptions/errors, retries/timeouts, rollback/cleanup, cancellation, concurrency safety, logging, security failures, and recovery across component boundaries. Review time/memory/disk/network/user-wait implications and stated limits. Verify the thesis honestly lists known bugs, unimplemented plans, technical debt, maintenance issues, and future work.

Missing error handling in a low-risk helper need not lose the point; systemic unsafe behavior, hidden failures, resource leaks, unbounded work, or undisclosed material limitations should.

## Safe execution and tools

- Prefer read-only inspection first: file inventory, manifests, history, dependency graph, static analysis, and tests.
- Run builds/checks only in an isolated, disposable environment with no production credentials or uncontrolled services.
- Do not install or execute opaque binaries unnecessarily.
- If accounts, mobile devices, paid services, private infrastructure, or destructive datasets are required, prepare a supervisor-run demo/check instead of claiming automated verification.

## Evidence output

For each C5 point, cite thesis pages and exact files/symbols/commits/check outputs. Record the commands and environment used for any reproducible check. Separate a code defect from a documentation defect and explain which clause each affects.
