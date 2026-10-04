# Contradiction Atlas

**Version:** 0.1  
**Status:** experimental

Contradiction Atlas maps conflicting claims **without forcing premature resolution**.

Research often contains statements that disagree on date, time, place, count, identity, sequence, cause, wording, or interpretation. A normal summary tends to choose one, average them together, or quietly discard the awkward one.

Contradiction Atlas keeps the disagreement visible.

> A contradiction is not a defect in the dataset. It is part of the evidence state.

## What it records

An atlas contains:

- sources
- individual claims
- source support for each claim
- explicit claim-to-claim conflicts
- the dimension of each conflict
- conflict status and status history
- optional resolution notes

Conflict dimensions include:

`date`, `time`, `location`, `count`, `identity`, `sequence`, `wording`, `causation`, `interpretation`, and `other`.

Conflict states are deliberately small:

- `open`
- `narrowed`
- `resolved`
- `insufficient-evidence`

A new conflict begins as **open**. The program does not select a winning claim.

## Quick start

```bash
python contradiction_atlas.py new atlas.json --title "Signal dispute"

python contradiction_atlas.py source atlas.json "Harbor log" \
  --kind primary --date 1904-11-03

python contradiction_atlas.py claim atlas.json \
  "The bell rang three times." --source S001

python contradiction_atlas.py claim atlas.json \
  "The bell rang twice."

python contradiction_atlas.py conflict atlas.json C001 C002 \
  --dimension count \
  --note "The accounts disagree on signal count."

python contradiction_atlas.py matrix atlas.json
python contradiction_atlas.py render atlas.json -o report.md
python contradiction_atlas.py mermaid atlas.json -o conflicts.mmd
```

## Outputs

Contradiction Atlas can produce:

- plain JSON
- a Markdown research report
- a Markdown conflict matrix
- a Mermaid graph of claim conflicts

## Example

The fictional example in [`examples/demo.json`](examples/demo.json) contains three claims and two different kinds of tension.

One conflict remains open. Another is marked `insufficient-evidence` because the available records do not justify choosing an interpretation.

See [`examples/demo.md`](examples/demo.md) and [`examples/demo.mmd`](examples/demo.mmd).

## What it does not do

Contradiction Atlas does not decide truth automatically.

It does not treat the oldest source as the winner.

It does not assume that two statements in tension are exact logical negations.

It does not require every contradiction to be resolved.

It preserves the structure of disagreement so later evidence can change only what it actually reaches.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License and reuse

**No reuse license has been granted.**

This public build is available for inspection and development by its maintainers. Do not assume that public visibility grants permission to copy, redistribute, modify, sell, incorporate, or relicense the code or documentation.

See [`COPYRIGHT.md`](COPYRIGHT.md).

## Working principle

Do not smooth the wrinkle until you know why it exists.
