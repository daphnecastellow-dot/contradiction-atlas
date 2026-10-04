# North Reach signal dispute: contradiction demo

_Contradiction Atlas format: `contradiction-atlas/0.1`_

## Claims

### C001

The bell rang three times shortly before midnight.

**Scope:** Signal count and time

**Sources:** S001 · Harbor master log

### C002

The bell rang twice after midnight.

**Scope:** Signal count and time

**Sources:** S002 · North Reach Gazette

### C003

The bell was not heard from the keeper station.

**Scope:** Whether the signal was audible at the station

**Sources:** S003 · Keeper interview transcript

## Conflicts

### X001 · count · open

**C001:** The bell rang three times shortly before midnight.

**C002:** The bell rang twice after midnight.

**Conflict note:** The early sources disagree on the number of rings.

### X002 · interpretation · insufficient-evidence

**C001:** The bell rang three times shortly before midnight.

**C003:** The bell was not heard from the keeper station.

**Conflict note:** One record reports a signal; another witness reports not hearing it. These statements are in tension but are not exact logical negations.

## Conflict matrix

| | C001 | C002 | C003 |
|---|---|---|---|
| **C001** | · | X001 · open | X002 · insufficient-evidence |
| **C002** | X001 · open | · |  |
| **C003** | X002 · insufficient-evidence |  | · |
