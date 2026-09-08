---
name: algorithm-recover
description: >
  TRIGGER: when an algorithm already has a phase-1 implementation but no formalization —
  when the user says "recover the formalization", "write the spec for this existing
  code", "document this algorithm", "reverse-engineer the pseudocode", "this was ported
  from Lush/Fortran/C and never written up", or asks for a specification of a kernel that
  is already running. Also trigger when /next-phase resolves a target whose phase key is
  `formalization` for an algorithm whose phase-1 file already exists.
  Do NOT trigger when neither the formalization nor the phase-1 file exists — that is the
  forward entrance, `dp-compile:algorithm-formalize`. Do NOT trigger to *amend* an
  existing formalization; that is an edit to a living document, not a recovery.
---

# algorithm-recover

Recover a `FORMALIZATION.md` from an implementation that already exists, so an algorithm
that never had a natural-language or pseudocode statement still ends the chain with one.

The forward chain assumes prose → pseudocode → Python. Real code does not always arrive
that way: a kernel translated from a legacy implementation in another language has a
reference, but it is source code in a language nobody here runs, and the nearest thing to
a specification may be an account someone wrote while reading it. This skill is the second
entrance, and it produces the same artifact at the same path, with the dependency edge
pointing the other way.

## What must not happen

> **A recovered formalization is not a description of the implementation. It is a
> specification the implementation is one instance of.**

The difference is the whole risk of this entrance, and it is easy to miss because both
documents look alike. A description is written by reading the code and saying what it
does; it agrees with the code by construction, so it can never contradict it. That matters
because phases 2, 3 and 4 translate *from the formalization*: if the document was itself
translated from phase 1, the chain gains a step and no independent check, and a defect in
phase 1 is now written down as the specification and propagated four times with the
document's authority behind it.

Three things keep the document from collapsing into a description, and none is optional:

1. **Independent evidence.** The legacy source the kernel was ported from, an account
   written about it, and any differential oracles the manifest declares. Where the code
   and that evidence disagree, the disagreement is a finding — it is either a deliberate
   deviation to be recorded, or a bug.
2. **Stating intent rather than mechanism.** "Minimise total description length in bits
   (min-plus)" is a specification. "Adds `-log2(p)` and takes the smaller" is a paraphrase
   of the code.
3. **The human review at the end**, which is the only step that can catch a document that
   ratified a bug.

Where none of the three is available — no legacy source, no account, no oracle, and no
reviewer who knows the algorithm — say so plainly in the document's `Notes` rather than
producing a confident description. A recovered formalization that names its own weakness
is useful; one that hides it is worse than none.

## The manifest comes first

Every path, command and oracle below is resolved through the consumer's root
`dp-compile.toml`, whose contract is `commands/references/manifest.md`. This skill knows
no repository's layout and must not assume one: if there is no manifest, stop and say so
rather than resolving paths under a layout the repository does not have.

## Prerequisites — verify before writing a line

1. **The phase-1 file exists**, at the path `[phases].python` gives, and **the
   formalization does not**, at the path `[phases].formalization` gives. If both exist,
   this is an amendment to a living document and not a recovery — stop and say so. If
   neither exists, hand off to `dp-compile:algorithm-formalize` using the `Skill` tool.

2. **The suite is green.** Run `[commands].build` then `[commands].test`. A failing test
   is evidence about the kernel that you are about to write a specification for, and it
   should be understood before, not after.

3. **Read `[project].invariants`.** They state what a kernel in this repository must
   satisfy, and they are the one input to a recovery that does not come from the code. An
   implementation that violates an invariant is a finding; a document that recovers the
   violation as the specification has laundered it.

4. **Read `[project].encoder`.** The kernel indexes arrays by integer code. What those
   codes mean, and which are reserved, lives in the encoder documents — and the
   formalization must name sentinels abstractly rather than by index (see the forward
   skill's gotcha on reserved symbols; it applies here unchanged).

5. **Check `[algorithms.<name>].oracles`.** Where the manifest declares oracles, they are
   the strongest independent evidence available and are used in Step 6. Their absence is
   not a blocker, but it changes what the recovered document can claim.

## Instructions

### Step 1: Read the implementation in full, and its tests with it

Read the whole phase-1 file, not the recurrence. Then read its tests. Three things come
out of the tests that the kernel alone does not give: which behaviours someone thought
were worth pinning, which inputs are considered in range, and — from the test names and
comments — the vocabulary the repository uses for this algorithm.

Read module docstrings and comments as **claims, not narration**. A well-maintained kernel
often states its own semiring, its own geometry, and its own deviations from the source it
was ported from, with citations. That is a gift: it turns most of Steps 3–5 into checking
rather than reconstruction. It is still a claim, and Step 6's oracle is what checks it.

### Step 2: Locate the legacy source and any account of it

The kernel was translated from something. Find it, and find anything written about it.
Three cases, and which one you are in belongs in the document:

- **The legacy source is in the repository** (an imported tree, a vendored directory).
  Cite it by path and commit. It is the primary evidence, and every deviation in Step 5 is
  a difference between it and the phase-1 file.
- **An account of it exists but the source does not.** Someone read the original and wrote
  down what it did. Cite the account, and say that the original itself was not consulted —
  a reviewer needs to know which claims rest on a reading rather than on the code.
- **Neither exists.** The kernel is the only artifact. Say so; the document then rests on
  Steps 3, 4 and the review, and its `Notes` must record that it has no independent
  evidence behind it.

Do not translate the legacy source afresh. It is evidence about what the algorithm is, not
a second implementation to be reconciled line by line.

### Step 3: Recover the recurrence, and render it fresh

Write the recurrence in the repository's pseudocode conventions
(`../algorithm-formalize/references/pseudocode-conventions-DP.md`), from the *behaviour*
the code implements rather than from its statements.

**Rendering fresh means the same thing here as in the forward skill, and for a sharper
reason.** Transliterating the loops back into pseudocode produces a document that reads
like the code with the types removed, and inherits every structural choice the
implementation made for reasons that have nothing to do with the algorithm — a hoisted
temporary, a fused loop, a buffer reused to save an allocation. Those are implementation
decisions, and phase 2 must be free to make different ones.

The test is simple: **if the pseudocode would have to change when phase 1 is optimised
without changing its results, it is describing the implementation.**

### Step 4: Surface what the code assumes but never says

The forward entrance recovers unnamed assumptions from a paper. Here they are recovered
from an implementation, where the evidence is different in kind — an assumption in code is
visible as an arithmetic choice rather than as an omission.

- **The objective and its direction.** Read it off the accumulation and the comparison, and
  state the semiring: max-plus, min-plus, max-product. **A domain change hides here.** A
  kernel that accumulates `-log2(p)` is minimising a description length in bits, which
  grows as the probability falls — so a `min` in the source is not a hint that the
  algorithm minimises probability, and a variable named for a probability may hold bits.
  Follow the values through whatever function performs the domain change; that function is
  usually the only place it happens.
- **Index geometry.** Count the array shapes rather than the loops. A path over *N*
  observations that visits *N + 1* states shows up as an output array one longer than its
  input, and that asymmetry is a property of the algorithm the document must state — not
  an off-by-one to be tidied.
- **Where the recurrence's factors come from.** A factor indexed by two endpoints cannot
  be hoisted out of the inner loop; one indexed by a single endpoint can. Which it is
  changes the recurrence and not merely the notation, and the code answers it directly.
- **The tie-breaking rule.** Read it off the comparison operator: `<` keeps the first
  candidate found, `<=` keeps the last, and the iteration order decides what "first"
  means. **This is contract**, so it goes in the document even though — and precisely
  because — no test may currently exercise it. See Step 6.
- **What the kernel does with impossible input.** A kernel that neither validates nor
  raises returns a sentinel that a wrapper interprets. That split is part of the
  specification, since every later phase must implement the same signature.

### Step 5: Write the two reverse-entrance sections

The template at `../algorithm-formalize/references/formalization-template.md` is canonical
for structure. Two of its sections take their reverse form here, and the template says so
in place:

- **`Source` → the implementation.** The Metadata `Source` row names the phase-1 file, by
  path and commit, and names the legacy source and any account beside it.
- **`Source Pseudocode` → `Source Implementation`.** Same purpose as the forward section —
  a reference snapshot so a reviewer can compare without opening anything else — so quote
  the *legacy* source's core routine where it exists, with its file and line range. Where
  it does not, omit the section as the forward entrance does, and say in `Notes` that the
  rendering had no second text to be checked against.
- **`Adaptations from Source` → `Deviations from the legacy source`.** Every place the
  phase-1 implementation behaves differently from what it was ported from, and every place
  it deliberately does not. `references/deviation-taxonomy.md` sets out the kinds and what
  each one does to the document.

**The formalization specifies the implementation's behaviour, not the legacy source's.**
Where a port deliberately fixed a defect, the recurrence states the fixed behaviour and the
deviations section records what the original did. Writing the original's behaviour into the
recurrence would specify the bug and make every later phase reproduce it.

### Step 6: Extract the test cases; do not invent them, and do not stop at them

The `Test Cases` section is **extracted** from what already exists — the phase-1 test
suite, any fixtures it reads, and the oracles the manifest declares — and each case
records where it came from. A case extracted from a passing test is a case the
implementation already satisfies, which is exactly why its provenance has to be visible: a
reader must be able to tell a specified behaviour from a ratified one.

Give every case one of three provenances, and say which:

| Provenance | What it is evidence of |
|---|---|
| **Oracle** | An output the *legacy* implementation produced, from `[algorithms.<name>].oracles`. The only evidence that is independent of this repository's code. |
| **Extracted** | An existing test's input and expected output. Evidence that the kernel is self-consistent and that someone once thought this mattered. |
| **Constructed** | Written now, from the recurrence, to cover something neither of the above reaches. |

**An oracle is not necessarily an equality check.** Where the port deliberately fixed a
defect, the oracle and the kernel are *expected* to differ, and the case states where and
why — **pinned exactly**, as an enumerated disagreement rather than a tolerance. A recovery
that quietly relaxes such a case until it passes has erased the finding that justified the
fix, and a relaxed bound silently accepts the next divergence too.

Each oracle also gets an entry in the document's `Differential oracles` section: what
produced it, which inputs it pairs with, whether the comparison is an equality check, where
it is not, and which TC carries it. The manifest lists where the files are; that section is
where what they *mean* is recorded, which is what a reviewer needs and what the manifest
cannot hold.

**Two things must be *covered*; construct them only where extraction did not already reach
them.** An extracted suite inherits every blind spot of the suite it came from, but a good
suite may have none — and a case written afresh alongside an existing test that already
makes the same assertion is duplication, not coverage. Check first, then construct:

- **Ties.** Learned or measured parameters essentially never tie, so a suite drawn from
  real data can pass while the tie-breaking rule is inverted. Construct the tie — uniform
  parameters, or an all-equal score matrix — and state the expected winner.
- **Degenerate parameters that the available data cannot produce.** A zero probability, an
  empty input, a single state, a disconnected topology. Real corpora are not adversarial;
  the next revision of the code often is.

State each case's precision level (exact, property-based, relational) exactly as the
forward entrance does.

**Do not assume the suite lacks these.** Deciding a case must be `constructed` without
looking is the mirror of the error the provenance rule exists to prevent: it labels as new
something the repository already had, and it reads to a later reviewer as though the
recovery found a gap. Where extraction covered everything and nothing was constructed, say
so — "this suite already covered the cases extraction usually misses" is a finding about the
repository worth recording in `Notes`.

### Step 7: Stamp the provenance header — it points backwards

Fill the template's `Derived from` row with the **phase-1 file's** path and the SHA-256 of
its contents, computed with that file's own `dp-compile` provenance line excluded.

This is the reverse of the forward entrance, where the row is empty because the document
derives from nothing in the repository. Here the direction is the point: the kernel is the
root, and the document is one of its dependents. Editing the kernel therefore marks the
formalization stale — correctly, since the specification was read off code that has since
moved — while editing the document marks nothing stale, because nothing was derived from
it. `commands/references/phase-detection.md` is where that graph is read.

Do not stamp a `derived-from` header onto the phase-1 file. It is the root of this
algorithm's graph and derives from nothing the plugin tracks.

### Step 8: Hard stop

**Create no implementation artifacts and change no existing ones.** Not the `.pyx`, not
either Numba phase, not a test file, not a backend-registry row — and, in particular, **do
not "fix" the phase-1 kernel to match the document you just wrote.** If the recovery found
a real defect, that is a finding to report; correcting it is a separate change with its own
review, and folding it into a documentation commit hides it.

**Report every specified case that no existing test implements**, by TC number, and say it
plainly: this document now specifies behaviour that nothing checks. The differential cases
are the ones that matter most here — phase 1 already exists, so writing their test code is
not a lifecycle phase and belongs to whoever owns the suite, but until it is written the
chain has no external check at all. `/next-phase` will refuse to advance past phase 1 while
a declared oracle is unexercised, and that refusal is the intended outcome rather than an
obstacle to route around.

Present the formalization to the user and say:

> "Review the recovered formalization — especially the deviations and any place the
> recurrence disagrees with the implementation. From here on this document is the
> specification, and the kernel is one implementation of it. When satisfied, commit it and
> run `/dp-compile:next-phase <name>`."

**The review matters more here than in the forward entrance**, and the user should be told
why: a forward formalization can be checked against its source paper, whereas this one was
read off the very code it now governs. The reviewer is the step that keeps a defect from
being promoted to a specification.

## What this skill does NOT do

- **No implementation code, and no edits to existing code.** Including the kernel it just
  read, and including a docstring "correction".
- **No re-translation of the legacy source.** It is evidence, not a second implementation.
- **No new tests.** Test *specifications* belong in the document; test *code* is phase 1's,
  and phase 1 already exists.
- **No amendment of an already-existing formalization.** That is an edit to a living
  document — make it directly, in its own commit.
- **No silent repair of a disagreement.** Where the code, the legacy source, an oracle and
  an invariant do not all agree, the disagreement is the most valuable thing the recovery
  produces. Report it; do not resolve it by choosing the one that makes the document
  tidiest.

## Gotchas

- **The document that agrees with the code perfectly is the suspicious one.** A recovery
  that surfaced no disagreement, no unstated assumption and no missing test case has
  probably described rather than specified. Say what evidence was available and what it
  ruled out, so a reader can judge which of the two happened.
- **A deliberately preserved convention is a deviation entry too.** Where the port matched
  the original on something it could reasonably have changed — a divide-by-zero returning
  zero rather than raising, say — that was a decision, and it is invisible in a diff.
  Recording only the differences loses exactly the choices a later cleanup will undo.
- **A comment citing a line number in the legacy source is a claim with a shelf life.**
  Check it against the file where the file is present; where it is not, quote the comment
  as a comment rather than restating it as fact.
- **A "harmless" defect not reproduced is still a deviation.** A type corrected on the way
  across changes no result today and may change one later. It belongs in the deviations
  section with the argument for why it was harmless, since that argument is what a future
  reader will want to re-check.
- **Do not hardcode a reserved code you read out of the kernel.** The kernel indexes by
  integer because it is downstream of the encoder; the formalization is upstream of it and
  names the sentinel abstractly. A repository's numbering has changed before.
- **Recovering a formalization does not make phase 1 stale.** The edge runs from the
  kernel to the document, so a fresh recovery leaves everything below it fresh. If phase
  detection reports phase 1 stale after a recovery, a header was stamped in the wrong
  direction — fix the header, not the kernel.

## Reference material

- `references/deviation-taxonomy.md` — the kinds of divergence between a port and its
  legacy source, and what each does to the recovered document.
- `../algorithm-formalize/references/formalization-template.md` — canonical structure,
  including the two sections that take a reverse form here.
- `../algorithm-formalize/references/pseudocode-conventions-DP.md` — the notation the
  recurrence is rendered in.
