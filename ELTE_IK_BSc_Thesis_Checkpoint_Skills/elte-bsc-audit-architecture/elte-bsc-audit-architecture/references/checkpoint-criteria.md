# Checkpoint 3 mandatory criteria

Apply every gate. Use N/A only for a conditional project feature with a concrete explanation.

## Expected evidence

- Substantive design document and legible figures.
- Approved proposal and checkpoint-2 requirements.
- Planned or registered final-exam topics.
- Confirmation of Thesis Consultation subject registration.
- Approved exceptions or scope changes.

## Mandatory gates

### C1 Design substance and figures

Provide at least ten substantive pages of design content and three to four high-quality figures. Exclude cover, contents, blank/padded pages, bibliography, and implementation listings from the count. Figures must be readable at normal PDF viewing size and referenced/explained in the text. Prefer vector output for text-heavy diagrams.

### C2 Architecture and separation

Describe system purpose and structure; subsystems/components/layers; responsibilities; interfaces; principal data/control flows; deployment assumptions; standards, technologies, development methods, tools, and components. Explain separation among UI or interaction, business/core logic, and data sources where applicable.

### C3 Business rules

State the important domain rules, invariants, validation, permissions, state transitions, and failure policies. Show where each rule is owned or enforced. A list of features is not a business-rule model.

### C4 Mandatory class diagram

Include a class diagram that represents the implemented/planned system's important classes or class-like types, relationships, multiplicities where meaningful, and key operations. It must correspond to named responsibilities and requirements, not be a generic framework dump or decorative auto-generated graph.

For a non-class-based system, only explicit supervisor approval can replace this gate; record the approved equivalent.

### C5 Data design

When persistence exists, document storage choice, entities/schema, relationships, constraints, lifecycle, and interfaces. A relational system should include an ERD or relational overview and enough field/table detail to guide implementation; address procedures, functions, triggers, migrations, or equivalent mechanisms when present.

When no persistence exists, explain transient data flow/state and mark persistence-specific details N/A.

### C6 Interaction design

For a GUI, show major screens, mockups/wireframes, navigation, menus, and important event handlers. For a CLI or API, document commands/endpoints, input/output, main request flows, and error behavior. Mark a UI-only element N/A only when an equivalent interaction model is present.

### C7 Core logic or scientific model

Describe the core application logic, algorithms, state transitions, or technical/scientific model at design level. Inputs, outputs, invariants, and component responsibilities must be clear enough to implement without inventing the main design.

### C8 Requirement and contribution traceability

Trace all high-priority requirements and each approved complex contribution to components, interactions, data, and acceptance evidence. Identify orphan requirements, components with no justified requirement, and approved changes.

### C9 Design rationale and level

Justify major architectural, data, pattern, interface, and deployment choices with project constraints and alternatives where meaningful. Keep low-level library calls and code listings out of the design rationale unless the thesis is fundamentally about those languages/tools.

### C10 Final-exam topic integration

Apply the semester rule in source-policy.md.

Outside an applicable transition, identify exactly three topics from the official list and map their relevant subtopics naturally into the design and planned implementation. Under a verified transition, require at least a credible provisional mapping and report unfinished registration as a major warning.

Do not accept generic textbook paragraphs or section labels such as Exam Topic 1 as evidence.

### C11 Consultation subject registration

Confirm registration for the Thesis Consultation subject offered with the supervisor as lecturer, or record an applicable approved administrative exception.

### C12 Internal consistency and implementability

Names, boundaries, technologies, classes, interfaces, data, rules, requirements, and diagrams agree across artifacts. Deliberate deviations are explicit and approved. The design is specific enough that the principal source structure could be implemented from it.

## Non-blocking suggestions

May include improved notation, extra sequence/activity/deployment views, stronger alternatives analysis, or early final-exam coverage. Do not fail a complete project merely because every optional UML type is absent, unless the student selected Object-Oriented Modelling and the topic-specific requirement applies.
