# Solution plan

Supervisor guidance checked 2026-09-10 sets at least 10 pages and 3-4 high-quality figures for design. Treat length and figure count as minimum evidence gates, not proof of quality. The plan should be precise enough that a competent developer could implement the essential system from it.

## C4.1 Architecture

Require a project-specific architecture showing:

- system boundary, actors/external systems, subsystems/components/layers, and responsibilities;
- UI/presentation, logic/domain, and data separation where relevant;
- standards, protocols, methods, and important interfaces;
- runtime/deployment topology where it affects behavior;
- technology choices and trade-offs at the appropriate abstraction level;
- mapping from major requirements and complex features to architectural elements.

Cross-check names, boundaries, dependencies, and technology claims against repository structure and code. Do not reward a generic cloud/framework diagram.

## C4.2 Data model and persistence

For relational systems, require an ERD and derived schema with keys, cardinalities, integrity constraints, important fields/types, migrations, indexes, and stored procedures/triggers where used. For NoSQL, files, cloud stores, caches, streams, or model/vector stores, require the equivalent explicit structure, identity, relationships, validation, lifecycle, and consistency decisions.

Also inspect interfaces, data flow, serialization, ownership, privacy/security, backup/migration, and scale assumptions where applicable. Cross-check diagrams against schema/migration/ORM/configuration files. For a project with no persistence, require an explicit and defensible account of transient/state data and the project-appropriate equivalent; do not award by omission.

## C4.3 Module or class design

Require the major modules/classes/packages, responsibilities, relationships, and important methods/operations with input, output, side effects, invariants, and error contracts. The design should expose how each complex feature is decomposed.

Use diagrams appropriate to the paradigm. For OOP projects, verify the class diagram against code and distinguish inheritance, realization, association, aggregation, and composition correctly. If Object-Oriented Modelling is a selected exam topic, apply its four-diagram requirement from the exam-topic reference. For non-OOP projects, accept a rigorous module/component/function design equivalent.

## C4.4 Interaction design

For GUI systems, require major screens, navigation, states, validation, roles, accessibility-relevant behavior, and key event-to-operation paths. For CLI/API/library/service systems, require commands/endpoints/public interfaces, request/input and response/output contracts, errors/statuses, authentication/authorization, and important interaction sequences.

Verify the design covers all promised workflows and matches final routes, commands, or interfaces. Do not force UI artifacts onto headless systems; require the equivalent interaction contract.

## Design versus implementation

The supervisor guidance generally excludes low-level tool/library/language notes from design unless they are genuine design inputs or the thesis is about those tools/languages. Flag implementation detail masquerading as design, but do not penalize justified design constraints. If a decision appears in both chapters, each treatment must add distinct value.

## Evidence output

For each C4 point, cite the relevant pages/figures plus corroborating code paths. Record stale diagrams, missing interfaces, unexplained symbols, orphan components, and undocumented deviations. Tie every repair to the exact absent decision or relationship.
