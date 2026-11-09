# Spec Delta

## ADDED Requirements

### Requirement: Synthetic OpenSpec fixture ownership
Automated hook integration, terminal, and native acceptance fixtures SHALL generate self-contained OpenSpec projects from test-owned inputs. Fixture preparation SHALL NOT read or copy the contributor's OpenSpec tree, inherit its context/rules/store pointers, or depend on real spec/change identities. Preparing a fixture SHALL NOT modify contributor files or Git state.

#### Scenario: Contributor OpenSpec content is unavailable
- **WHEN** fixture preparation is prevented from reading the contributor's OpenSpec tree
- **THEN** integration/terminal and native acceptance fixture construction SHALL still succeed with their synthetic inputs
- **AND** the generated local configuration SHALL select the temporary fixture project

#### Scenario: Repository planning lifecycle changes
- **WHEN** real specs or changes are added, edited, or archived in the contributor's repository
- **THEN** the generated fixture content and its expected validation identities SHALL remain unchanged
- **AND** no historical real change SHALL need to remain active for test success

### Requirement: Real OpenSpec validation of synthetic scenarios
Real-CLI hook acceptance SHALL validate synthetic projects with the existing pinned OpenSpec command. Dedicated integration scenarios SHALL use fresh repositories and assert native codes, report validity, fixture roots, expected items, seven outcomes, and unchanged tracked state. Native acceptance SHALL retain equivalent evidence for its controlled successful and invalid-delta steps. CLI doubles SHALL NOT replace real acceptance coverage.

#### Scenario: Valid specs without active changes
- **WHEN** the synthetic project contains a valid durable spec and no active changes
- **THEN** the real CLI SHALL exit zero and report the expected valid spec
- **AND** hook acceptance SHALL succeed without requiring any change item

#### Scenario: Valid change with unfinished tasks
- **WHEN** the synthetic project contains a valid durable spec and a valid active delta with an unchecked implementation task
- **THEN** the real CLI SHALL exit zero and report the expected valid synthetic spec and change
- **AND** the unfinished task SHALL remain unchanged

#### Scenario: Invalid active delta
- **WHEN** the synthetic project contains an active delta missing a required scenario
- **THEN** the real CLI SHALL exit nonzero and identify the expected synthetic change as invalid
- **AND** the hook SHALL retain the valid native failure report and all seven validation outcomes

#### Scenario: Archived content is excluded
- **WHEN** the synthetic project's archive contains an invalid delta and unfinished tasks
- **THEN** valid durable specs SHALL still pass the real CLI validation
- **AND** the archived identity SHALL be absent from the validated item set
- **AND** archived files SHALL remain unchanged
