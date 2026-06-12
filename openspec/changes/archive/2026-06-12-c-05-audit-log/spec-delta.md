## ADDED Requirements

### Requirement: Audit Logging Capability
WHEN an action is performed that modifies system state,
the system SHALL record the details of the action in an immutable, append-only audit log.

#### Scenario: Successful Action Logging
GIVEN a critical action performed by an authorized user
WHEN the action is completed
THEN the system generates an audit log entry containing:
    - User identifier
    - Action type
    - Timestamp
    - State changes
AND the system persists the entry to the audit log store
AND the entry cannot be modified or deleted.

#### Scenario: Audit Log Integrity
GIVEN an audit log entry
WHEN an unauthorized attempt is made to modify or delete the entry
THEN the system rejects the operation
AND the system records an security alert.
