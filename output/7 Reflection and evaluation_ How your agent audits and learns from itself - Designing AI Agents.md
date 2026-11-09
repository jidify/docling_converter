# Reflection and evaluation: How your agent audits and learns from itself

listen

watch

buy the book

### This chapter covers

- Using feedback to improve an agent's current work and future behavior
- Refining a current artifact with the Generator-Critic pattern
- Recovering a failed task within a bounded Self-Heal Loop
- Admitting reusable capabilities through the Skill Package pattern
- Recalling validated lessons through the Experience Replay pattern
- Choosing evidence that can reveal the failure under investigation

*"An unexamined life is not worth living."*

- Socrates, in Plato's Apology 38a

An engineer building evaluation environments told me about an agent that added another safeguard whenever a new build failed. The safeguard addressed that failure, so the system kept it. The next failure led to another safeguard and another local check.

After about two months, the agent had accumulated dozens of constraints. The environments were more stable, but a build that had once taken about five minutes now took thirty minutes and sometimes close to an hour. Some safeguards overlapped while others worked against one another, even though each repair had made sense when it was added. Together, they had become a burden.

That case changed how I thought about reflection. I had often approached it as a second pass over an answer: inspect the result, find a problem, and try again. The environment-building agent was already doing that, and its local checks were useful. The problem appeared only when the team looked across many runs and saw what the repairs had accumulated.

The agent had responded reasonably to the evidence available in each run. The system lacked a wider process that could compare repairs, measure their combined cost, merge overlapping rules, and remove rules that no longer helped. A local pass justified the next step. It could not show that the whole system was improving.

In this chapter, you will build feedback paths for Argus that improve current work without turning every local fix into a permanent rule. You will start with artifact review and bounded recovery, then add the checks that decide which Skills and lessons can be reused on later tasks. The Python examples make those decisions explicit: what the agent may change, how the system verifies it, and when to stop or hand control back. You will also choose evaluation signals that expose accumulated cost and regressions across runs.

## 7.1 What is reflection?

Reflection is the engineering of feedback that is allowed to change something. The change may be small, such as revising the current answer, or persistent, such as admitting a Skill that later tasks can use. A production design has to answer three questions:

reflection

1. What can the feedback actually see?
2. When will the result of the change become known?
3. What is the agent allowed to change in response?

The four reflection patterns give the change a different place to live. Their canonical coordinates and changed objects appear in table 7.1.

reflection pattern

##### Table 7.1 The four reflection patterns

| Pattern           | Coordinate             | What may improve                                |
|-------------------|------------------------|-------------------------------------------------|
| Generator-Critic  | Reflection × Chain     | The current artifact                            |
| Self-Heal Loop    | Reflection × Loop      | The current execution and bounded working state |
| Skill Package     | Reflection × Route     | A reusable capability selected for later tasks  |
| Experience Replay | Reflection × Hierarchy | The agent's judgment through validated lessons  |

evaluator

The first two patterns work before the current task ends. The latter two alter what the agent can carry into later work. The delay before a result becomes known is a separate question from how long a change may affect behavior.

Every pattern needs evidence before a change is trusted, and that evidence must match the claim being made. A unit test can establish that one behavior passed under its test conditions. It cannot measure the cost of dozens of patches across two months. That claim needs a wider view. Table 7.2 previews the evidence, authority, and stopping decision for each pattern.

evidence

##### Table 7.2 Evidence and authority across the four patterns

| Pattern           | Primary evidence                                               | Change authority                           | Persistence               | Main stop                              |
|-------------------|----------------------------------------------------------------|--------------------------------------------|---------------------------|----------------------------------------|
| Generator-Critic  | Criteria, source material, tests, or tool results              | Revise the current artifact                | Current delivery          | Accept, stop, or exhaust review budget |
| Self-Heal Loop    | Failure signal, protected verifier, and regression results     | Repair bounded execution and working state | Current task              | Recover, roll back, or hand off        |
| Skill Package     | Isolated, coexistence, and trial evidence                      | Admit and route a versioned capability     | Across tasks              | Activate, reject, deprecate, or retire |
| Experience Replay | Traces, independent cases, causal evidence, and later outcomes | Admit and recall scoped advice             | Across tasks within scope | Replay, withhold, conflict, or retire  |

trajectory

**Recap Chapter 7 intro and 7.1 intro** to the AI assistant

type

### 7.1.1 Why another pass is not enough

Research on intrinsic self-correction explains part of the problem. An LLM asked to reconsider its reasoning without new evidence may improve an answer, leave it unchanged, or revise a correct answer into an incorrect one [1, 2]. Because the second pass remains a probabilistic generation, its fluency does not tell us whether it found a real error.

self-correction

Reflection becomes more dependable when verification is easier to ground than generation. Writing a correct program may be difficult; compiling it and running a focused regression test are comparatively direct. Producing a financial analysis may be difficult; recomputing its arithmetic with a tool is direct. CRITIC showed how tool-interactive feedback can improve correction over ungrounded critique [3]. Self-Refine showed that iterative feedback can improve results across varied tasks [4]. These findings lead to an engineering choice: decide what evidence the reviewer receives and what that evidence can establish.

reflection

verification

evaluator

Self-Refine

A second model can add useful separation, but model count and model identity do not establish an independent review by themselves. A Critic is useful when it starts from a perspective, criterion, context, or body of evidence that the Generator did not use. The same model can provide that separation when its review frame and evidence differ. Two model families can still repeat the same assumption. For consequential work, tests, tool results, source documents, human judgment, or observed outcomes strengthen the review.

independence

Evaluation therefore enters alongside each reflection pattern: the current artifact beside Generator-Critic, recovery and regression beside Self-Heal Loop, admission and coexistence beside Skill Package, and the effect of recalled lessons beside Experience Replay. Section 7.7 consolidates these signals.

evaluation

generator-critic loop

**Recap 7.1.1** to the AI assistant

type

## 7.2 Pattern: Generator-Critic

Generator-Critic separates production from review. A Generator creates an artifact, a Critic examines it against stated criteria and available evidence, and the Generator revises the same artifact or delivers it when the review is satisfied.

generator

In the two-dimensional framework, Generator-Critic occupies Reflection × Chain. Its canonical structure is `generate -> critique -> revise`. One traversal can produce the delivered result. A bounded return to the Critic is useful when another review is worth its cost, but repetition does not change the pattern's Chain coordinate.

##### Critical design decision: What can the Critic see that the Generator did not?

**Coordinates:** Reflection × Chain

**Engineering ancestors:** Code review, editorial review, and quality assurance

Use Generator-Critic when a current artifact benefits from a separate review path. Decide which version is under review, the criteria and evidence available to the Critic, permitted verdicts, and the stop policy. If the Critic receives the same assumptions and evidence as the Generator, additional reviews can reproduce the same blind spot. Measure confirmed-issue precision, quality change, oscillation, latency, and cost.

confirmed-issue precision

### 7.2.1 One artifact, a different line of inquiry

One production data-analysis team used an agent to generate SQL. People reviewed every query at first, but the team added model-based review as volume grew. Incorrect SQL and incorrect results still reached users when generation and review followed the same model preferences. In the team's tests, cross-model review found problems that same-model review had missed.

cross-model review

Changing the model helped in that case because it changed the line of inquiry. If the Generator chose a query plan because it assumed a join key was unique, a Critic that merely paraphrases the query may preserve the assumption. A Critic with schema constraints, sampled records, execution results, or an explicit instruction to test join cardinality can expose it. The added value comes from what the review can examine.

Feedback scope is the part of the artifact and its consequences that a check can actually observe. A parser can check SQL syntax, while a read-only execution can reveal whether the query runs, and a test with expected rows can check a known behavior. A domain reviewer may still be needed to decide whether the result answers the business question. Each Critic should make claims within the scope of its evidence.

feedback scope

evaluator

Generator-Critic remains a reflection pattern, while critique returns to the producing process to improve the same artifact. When participants take opposing responsibility for a contested claim and a judge must resolve the evidence, the design becomes Adversarial Review in chapter 8.

generator-critic loop

critique

##### Figure 7.1 The Generator-Critic chain. The Critic receives one artifact version, explicit criteria, and evidence; a bounded return permits another review.

![Image](7%20Reflection%20and%20evaluation_%20How%20your%20agent%20audits%20and%20learns%20from%20itself%20-%20Designing%20AI%20Agents_images/image_000000_8437519707110e937250d8cadc360a49a7d7d5cd57cd4d4d0c0b74f34f54ca5c.png)

Four benefits and their corresponding limits appear in table 7.3. None of them removes the need to define the Critic's scope.

##### Table 7.3 Generator-Critic trade-offs

| Advantage                                                        | Limitation                                                    |
|------------------------------------------------------------------|---------------------------------------------------------------|
| A separate review path can expose an assumption missed during    | Shared criteria and context can reproduce the same blind spot |
|    generation                                                    |                                                               |
| Tool evidence can ground a finding in observable behavior        | Every tool covers only the behavior it checks                 |
| Versioned critique creates an audit trail from issue to revision | Additional reviews add latency and cost                       |
| A stop policy bounds overcorrection and oscillation              | A poor stop policy may retain a weaker late version           |

The review path can take several forms. The comparison in table 7.4 distinguishes them by what they add, rather than by the number of agent labels in the implementation.

##### Table 7.4 Three Critic implementations

| Review mode                 | What changes                                         | Useful evidence                                           | Main risk                                                        |
|-----------------------------|------------------------------------------------------|-----------------------------------------------------------|------------------------------------------------------------------|
| Rubric-grounded             | Criteria and responsibility                          | Explicit rubric, required behavior, examples              | The rubric may preserve the Generator's assumptions              |
| Context- or model-separated | Context slice, prompt, model, or role responsibility | Independent sources, alternative plan, domain constraints | Different labels may still follow the same reasoning path        |
| Tool-grounded               | Evidence source                                      | Tests, linters, calculators, schema checks, retrieval     | The tool may cover too little or become writable by the producer |

Human review fits the same design when the artifact requires judgment that the automated evidence cannot supply. The reviewer still needs a clear question and the relevant evidence. Sending a person the entire trajectory without a review scope merely transfers the search cost.

**Recap 7.2 intro and 7.2.1** to the AI assistant

type

### 7.2.2 Design the Critic before adding iterations

A useful Critic contract contains the fields in table 7.5. The contract matters more than whether the Critic is implemented as the same model, another model, a tool, or a person.

critic contract

##### Table 7.5 A Critic contract

| Field             | Question it answers                 | Example                                                  |
|-------------------|-------------------------------------|----------------------------------------------------------|
| Artifact identity | What exact version is under review? | Commit, document revision, or response ID                |
| Criteria          | What counts as an issue?            | Required behavior, rubric, or invariant                  |
| Evidence          | What may the Critic consult?        | Tests, source documents, tool output, or samples         |
| Permitted result  | What may the Critic return?         | Accept, request revision, or stop as unresolved          |
| Stop policy       | When does review end?               | Acceptance, budget limit, no improvement, or oscillation |

Iteration is a budget decision. Record the first artifact, every critique, the revision it caused, and the best artifact seen so far. Stop when the artifact meets the criteria, the Critic has no actionable change, the same issues begin to alternate, or the review budget is exhausted. Preserve the best known artifact so a late overcorrection cannot erase an earlier improvement.

iteration

critique

Useful measurements include confirmed-issue precision, change in task quality after critique, iterations to acceptance, oscillation rate, latency, and cost. Thresholds should come from a baseline on the team's own tasks. A universal score has little meaning until it has been calibrated against the outcomes the team cares about.

confirmed-issue precision

critique quality change

iterations to acceptance

oscillation rate

### 7.2.3 Building Generator-Critic

The first listing defines the review objects. Evidence identifiers are stored beside the verdict so a finding can be traced to its supporting source.

##### Listing 7.1 Review contract and critique records

```
from dataclasses import dataclass, field

from typing import Literal

 

 

@dataclass(frozen=True)

class EvidenceItem:

    evidence_id: str

    source: str

    passed: bool | None

    detail: str

 

 

@dataclass(frozen=True)

class Critique:

    verdict: Literal["accept", "revise", "stop"]

    issues: tuple[str, ...] = ()

    evidence_ids: tuple[str, ...] = ()

 

 

@dataclass(frozen=True)

class ReviewContract:

    criteria: tuple[str, ...]

    max_reviews: int
```

A

B

The next listing keeps evidence collection outside the Critic. Each check returns a durable identifier, a pass state when one applies, and its detail.

evaluator

##### Listing 7.2 Gathering evidence through independent checks

```
def gather_review_evidence(

    task: str,

    artifact: str,

    checks,

) -> tuple[EvidenceItem, ...]:

    items = []

    for check in checks:

        evidence_id, passed, detail = check(task, artifact)

        items.append(EvidenceItem(

            evidence_id=evidence_id,

            source=check.__name__,

            passed=passed,

            detail=detail,

        ))

    return tuple(items)
```

One review traversal returns both the Critique and the exact artifact version that was inspected, as shown next.

critique

##### Listing 7.3 Reviewing one artifact version

```
@dataclass(frozen=True)

class ReviewStep:

    artifact: str

    evidence: tuple[EvidenceItem, ...]

    critique: Critique

 

 

def review_once(task, artifact, contract, critic, checks):

    evidence = gather_review_evidence(task, artifact, checks)

    report = critic(task, artifact, contract, evidence)

    return ReviewStep(artifact, evidence, report)
```

The bounded implementation adds iteration and best-version preservation. Its `select_best` function uses domain evidence, such as regression results or a calibrated rubric. A second model's preference alone is insufficient.

best-version preservation

evidence

##### Listing 7.4 A bounded Generator-Critic chain

```
@dataclass

class ReviewResult:

    artifact: str

    status: str

    history: list[ReviewStep] = field(default_factory=list)

 

 

def generator_critic(

    task,

    contract,

    generate,

    revise,

    critic,

    checks,

    select_best,

):

    artifact = generate(task)

    versions = [artifact]

    history = []

 

    for _ in range(contract.max_reviews):

        step = review_once(

            task,

            artifact,

            contract,

            critic,

            checks,

        )

        history.append(step)

        if step.critique.verdict == "accept":

            return ReviewResult(artifact, "accepted", history)

        if step.critique.verdict == "stop":

            best = select_best(task, versions, checks)

            return ReviewResult(best, "unresolved", history)

 

        artifact = revise(task, artifact, step.critique)

        versions.append(artifact)

 

    best = select_best(task, versions, checks)

    return ReviewResult(best, "budget_exhausted", history)
```

A

B

C

**Recap 7.2.2 and 7.2.3** to the AI assistant

type

### 7.2.4 When Generator-Critic breaks

**Shared blind spot.** The Critic restates the Generator's reasoning and misses the same assumption. Give the Critic different criteria, context, or evidence. A different model helps only when it changes the review path.

shared blind spot

generator

**Critique hallucination.** The Critic reports an issue that the evidence does not support, and the Generator damages a correct artifact while trying to fix it. Preserve artifact versions and require findings to cite a criterion or evidence item.

hallucination

evaluator

**Rubber-stamp acceptance.** The Critic produces a high score without checking the relevant behavior. Calibrate scores against known examples and record criterion-level findings instead of one unexplained number. Self-preference and position effects in model-based judging make this calibration necessary [5, 6].

rubber-stamp acceptance

self-enhancement bias

position effect

judge-based evaluation

**Oscillation.** One revision fixes A and reintroduces B; the next reverses the choice. Detect repeated issue and artifact signatures, return the best known version, and hand unresolved trade-offs to a wider decision process.

oscillation

**Mutable evidence.** The producing process can change the test, rubric, or threshold that judges its work. Protect the evidence channel. A legitimate change to a test or acceptance criterion should travel through a separate review path.

mutable evidence

Generator-Critic improves an artifact. The next pattern begins when a failure has stopped the task, and the agent receives permission to change more than the artifact itself.

generator-critic loop

**Recap 7.2.4** to the AI assistant

type

## 7.3 Pattern: Self-Heal Loop

Self-Heal Loop recovers a failed task through a bounded cycle of diagnosis, repair, verification, rollback, and handoff. Its recovery envelope may include execution steps, tool arguments, temporary state, or an isolated part of the environment. The agent must verify the effect of every change.

fail-diagnose-fix-verify loop

repair

recovery envelope

verification

In the two-dimensional framework, Self-Heal Loop occupies Reflection × Loop. The loop is structural because a failed task cannot proceed unchanged. Each attempt is either accepted or rolled back. The loop then recovers, continues within its budget, or hands the task to a person or another authorized process.

reflection

rollback

##### Critical design decision: What may the recovery loop change, and what must remain protected?

**Coordinates:** Reflection × Loop

**Engineering ancestors:** Test-driven development, automated remediation, and transactional recovery

Use Self-Heal Loop when a reliable failure signal exists and repair can be isolated, verified, and reversed. Declare writable and protected state, capture a baseline, keep the verifier outside the repair path, and bound the attempts. A loop that can rewrite its own tests or cannot restore its baseline has no trustworthy recovery claim. Measure recovery and regression rates, rollback success, attempts, cost, and handoff.

protected state

baseline

verifier

regression rate

rollback success

### 7.3.1 Recovery requires permission and responsibility

A failed tool call gives a simple example. Suppose an agent invokes a command with a parameter that a newer tool version has removed. The error identifies the invalid argument. Inside a sandbox, the agent can inspect the current tool contract, revise the invocation, and run the check again. The repair remains bounded, and the verifier can tell whether it worked.

tool contract

The boundary becomes clearer when a failure is diagnosable, but the missing knowledge is not. An omitted execution step may be diagnosable and repairable. Repeating the loop cannot supply authoritative domain knowledge that the system does not possess. The appropriate outcome in the latter case is to request the missing knowledge or hand the task to someone who has it.

Modification authority is the set of artifacts, actions, and state that a recovery loop is permitted to change. Greater authority creates greater responsibility. A Self-Heal Loop needs to verify every mutation, preserve a rollback point, stop when progress stalls, and produce a useful handoff when the failure lies outside its boundary.

modification authority

A conservative authority policy treats the current artifact, allow-listed tool arguments, and isolated temporary state as writable. The verifier, acceptance criteria, and protected tests remain read-only. Persistent Skills, shared rules, and configuration changes begin as proposals. Production policy, credentials, the main branch, and safety boundaries stay outside the loop.

Self-Heal can propose a persistent change to shared rules or configuration. It cannot merge or retire that change within the current task. A separate cross-run process may automate a low-risk merge or retirement only when the change is reversible and passes the relevant regression checks. A change that affects safety policy, production boundaries, or several task families remains a proposal until a person with the required authority approves it. The process that proposes a repair should not be free to rewrite the evidence used to approve that repair.

##### Figure 7.2 The Self-Heal Loop. The agent captures a baseline, diagnoses a failure, checks repair authority, applies a change atomically, verifies it, and either recovers, retries, rolls back, or hands off.

![Image](7%20Reflection%20and%20evaluation_%20How%20your%20agent%20audits%20and%20learns%20from%20itself%20-%20Designing%20AI%20Agents_images/image_000001_6051cf058d4d78d24b8318fbad970bf6172cd1271bfbf6dbefbc3649cbc4b3ba.png)

The trade-offs in table 7.6 show why the recovery envelope must stay explicit.

##### Table 7.6 Self-Heal Loop trade-offs

| Advantage                                                     | Limitation                                                    |
|---------------------------------------------------------------|---------------------------------------------------------------|
| A verifier can turn a failure into a concrete recovery signal | The loop cannot repair a condition it cannot observe or judge |
| Bounded write authority permits automatic recovery inside a   | Greater authority increases the damage from a wrong diagnosis |
|    sandbox                                                    |                                                               |
| Snapshots and atomic changes make rollback testable           | Shared external state may remain difficult to restore         |
| Attempt history supports diagnosis and handoff                | Repeated repair adds latency, cost, and state complexity      |

Spotify's Honk makes the protected-verifier boundary concrete. The coding agent can edit files and request verification, but component-specific formatting, build, and test checks run behind independent verifiers whose implementations are not exposed to the agent. Before Honk opens a pull request, every applicable verifier must pass [7]. The repair loop may change the candidate; it cannot rewrite the evidence used to accept it.

**Recap 7.3 intro and 7.3.1** to the AI assistant

type

### 7.3.2 The fail-diagnose-fix-verify loop

The sequence is practical:

1. **Capture.** Record the failure, relevant state, tool and dependency versions, and a restorable baseline. capture
2. **Diagnose.** Form a cause hypothesis from the failure evidence and prior attempts. hypothesis
3. **Propose.** Generate a repair inside the declared writable scope.
4. **Check authority.** Reject or escalate a proposal that touches protected evidence, policy, credentials, or state outside the sandbox.
5. **Apply atomically.** Create a checkpoint that can be reversed without guessing which changes belong to which attempt. checkpointing
6. **Verify.** Run protected checks for the original failure and the surrounding regression set.
7. **Decide.** Return success, continue within budget, roll back, or hand off.

A cost-ordered verifier cascade makes this practical. Run a schema or format check before a linter, a linter before a build, and a focused test before a larger regression suite when those checks apply. Cheap failures can stop an attempt before expensive checks run. A model Critic may review a repair proposal before application, while the protected verifier still controls whether the task has recovered.

verifier cascade

### 7.3.3 Building Self-Heal Loop

The recovery data model defines the policy, proposal, verifier result, and mutable state. The policy comes from the surrounding system and remains outside the agent that proposes the repair.

recovery data model

verifier result

mutable state

##### Listing 7.5 Recovery policy and state records

```
@dataclass(frozen=True)

class RecoveryPolicy:

    max_attempts: int

    writable_paths: tuple[str, ...]

    protected_paths: tuple[str, ...]

    allowed_tools: frozenset[str]

 

 

@dataclass(frozen=True)

class RepairProposal:

    change: object

 

 

@dataclass(frozen=True)

class ChangeScope:

    paths: tuple[str, ...]

    tools: frozenset[str]

 

 

@dataclass(frozen=True)

class VerificationReport:

    passed: bool

    regressed: bool

    failure: str | None

    evidence_ids: tuple[str, ...]

 

 

@dataclass

class RecoveryState:

    original_failure: str

    failure: str

    baseline: object

    versions: dict[str, str]

    history: list[dict] = field(default_factory=list)
```

A

B

The following function captures the failure and baseline before the first mutation. The workspace owns the details of snapshotting files, temporary state, and relevant dependency versions.

workspace

snapshot

##### Listing 7.6 Capturing a restorable recovery baseline

```
def capture_recovery(workspace, failure: str) -> RecoveryState:

    return RecoveryState(

        original_failure=failure,

        failure=failure,

        baseline=workspace.snapshot(),

        versions=workspace.versions(),

    )
```

The trusted workspace derives the affected paths and tools from the structured change. It does not authorize a repair from scope metadata supplied by the agent. The authority check uses lexically normalized path roots and the allowed tool set. The workspace resolves symbolic links inside its sandbox and enforces the same policy again when the mutation is applied.

structured change

scope metadata

authority check

##### Listing 7.7 Checking a repair against its authority envelope

```
from pathlib import PurePosixPath

from posixpath import normpath

 

 

def under(path: str, root: str) -> bool:

    value = PurePosixPath(normpath(path))

    boundary = PurePosixPath(normpath(root))

    return value == boundary or boundary in value.parents

 

 

def repair_allowed(

    proposal: RepairProposal,

    policy: RecoveryPolicy,

    workspace,

) -> bool:

    scope: ChangeScope = workspace.inspect_change(proposal.change)

    if not scope.paths and not scope.tools:

        return False

    if not scope.tools <= policy.allowed_tools:

        return False

    if any(

        under(path, root)

        for path in scope.paths

        for root in policy.protected_paths

    ):

        return False

    return all(

        any(under(path, root) for root in policy.writable_paths)

        for path in scope.paths

    )
```

A

B

Each proposal receives a checkpoint before atomic application. The trusted executor rechecks the policy during the write. The function in the next listing restores the checkpoint when application raises an error, verification fails, or a regression appears.

checkpointing

atomic application

trusted executor

verification

##### Listing 7.8 Applying and verifying one repair attempt

```
def apply_and_verify(workspace, proposal, policy):

    checkpoint = workspace.snapshot()

    try:

        workspace.apply_atomic(proposal.change, policy)

        report = workspace.verify_protected()

    except Exception:

        workspace.restore(checkpoint)

        raise

    if not report.passed or report.regressed:

        workspace.restore(checkpoint)

    return report, checkpoint
```

The bounded loop joins these pieces. `no_progress` is supplied by the domain because a repeated compiler error, a worsening reconciliation, and an unchanged support diagnosis need different comparisons.

##### Listing 7.9 A policy-bounded Self-Heal Loop

```
def handoff(workspace, state, reason):

    workspace.restore(state.baseline)

    return {

        "status": "handed_off",

        "reason": reason,

        "original_failure": state.original_failure,

        "versions": state.versions,

        "baseline_restored": True,

        "history": state.history,

    }

 

 

def self_heal(failure, policy, workspace, diagnose, propose, no_progress):

    state = capture_recovery(workspace, failure)

 

    for attempt_no in range(policy.max_attempts):

        diagnosis = diagnose(state.failure, state.history)

        proposal = propose(diagnosis, policy)

        if not repair_allowed(proposal, policy, workspace):

            return handoff(workspace, state, "outside_authority")

 

        try:

            report, checkpoint = apply_and_verify(

                workspace,

                proposal,

                policy,

            )

        except Exception as error:

            state.history.append({

                "attempt": attempt_no + 1,

                "diagnosis": diagnosis,

                "proposal": proposal,

                "error": type(error).__name__,

            })

            return handoff(workspace, state, "apply_error")

        state.history.append({

            "attempt": attempt_no + 1,

            "diagnosis": diagnosis,

            "proposal": proposal,

            "checkpoint": checkpoint,

            "report": report,

        })

        if report.passed and not report.regressed:

            return {

                "status": "recovered",

                "artifact": workspace.artifact(),

                "result": workspace.result(),

                "history": state.history,

            }

        if report.regressed:

            return handoff(workspace, state, "regression")

        if no_progress(state.history):

            return handoff(workspace, state, "no_progress")

        state.failure = report.failure or state.failure

 

    return handoff(workspace, state, "budget_exhausted")
```

A

B

C

D

The handoff record should include the original failure, each diagnosis, the exact changes attempted, verifier results, dependency versions, and the restored baseline. This lets the next engineer continue the investigation without reconstructing it from scattered logs. A team may also preserve the failed branch or sandbox snapshot for diagnosis, provided that it cannot become production state accidentally.

handoff record

**Recap 7.3.2 and 7.3.3** to the AI assistant

type

### 7.3.4 When Self-Heal Loop breaks

**Missing oracle or knowledge.** The loop can observe a failure but cannot determine success or obtain the facts needed for repair. Stop and acquire the missing verifier, capability, or domain knowledge.

test oracle

**Verifier subversion.** The agent makes the test easier instead of making the system correct. Protect tests and acceptance criteria. If a test is obsolete, review its change separately from the production repair.

verifier subversion

**Whack-a-mole repair.** Each attempt replaces one failure with another. Track failure signatures, affected scope, and regression results. Roll back when the repair expands damage or stops making measurable progress.

whack-a-mole repair

failure signature

**Rollback gap.** Several attempts mutate shared state, and no exact baseline can be restored. Use isolated workspaces and atomic checkpoints before granting the agent write authority.

rollback gap

baseline

workspace isolation

checkpointing

**Local recovery with global degradation.** Every attempt passes its immediate check, yet retained repairs increase latency, cost, or conflict over time. This is the failure from the chapter opening. The online loop needs a cross-run view that measures accumulated constraints and proposes consolidation or retirement. Low-risk, reversible cleanup can run automatically after regression checks. Broader changes require human approval.

local recovery with global degradation

cross-run view

memory consolidation

retire

Track recovery rate together with regression rate, rollback success, attempts per task, time and tokens spent, handoff rate, and cross-run cost. A green test answers whether the current verifier passed. It does not establish that the system became simpler, faster, or better across tasks.

recovery success

regression rate

rollback success

attempts per task

handoff rate

Generator-Critic and Self-Heal Loop both finish within the current task. The next two patterns change the **reflection time scale**, the period for which a change may affect behavior. Skill Package decides whether a successful method should become an admitted capability for later tasks.

generator-critic loop

fail-diagnose-fix-verify loop

agent skill

**Recap 7.3.4** to the AI assistant

type

## 7.4 Pattern: Skill Package

Skill Package changes what the agent can carry into later tasks. It turns a successful, repeatable way of working into a versioned capability that may be selected again. In the two-dimensional framework, Skill Package sits at Reflection × Route. Reflection extracts and tests a possible capability. Route determines whether that capability applies to a new task and whether it is allowed to receive traffic. A general solver remains available when no admitted Skill fits.

AI agent

reflection

The closest software ancestor is a versioned plugin registry combined with a deployment promotion pipeline. A Skill has instructions or executable logic, an interface, dependencies, and a version. Agent systems add one more problem: the runtime has to decide which capability fits a task expressed in natural language. The design therefore has to cover the package's discovery metadata and the surrounding system's admission and routing decisions.

##### Critical design decision: When may a candidate Skill begin receiving traffic?

Coordinates: Reflection × Route Engineering ancestors: library functions, versioned plugins, and deployment promotion pipelines

Use Skill Package when a repeatable procedure may help later tasks. Define its applicability contract, version, and dependencies, then require isolated, coexistence, and bounded-trial evidence before traffic. A Skill that works alone can still steal traffic or conflict with the active library. Measure routing precision, task-family quality, coexistence regressions, latency, context cost, and rollback success.

applicability contract

coexistence regression

Voyager [8] provides an early research form of this pattern. After a successful task in Minecraft, it stores the verified JavaScript program in a skill library and retrieves relevant programs for later tasks. Complex Skills can compose simpler ones. The stable game environment leaves a harder production question open: what happens when dependencies, traffic, and neighboring Skills change?

skill library

Claude Code gives the package a concrete filesystem shape. A Skill has a `SKILL.md` entry point whose description helps the runtime decide when it applies. References, examples, and helper scripts can remain in supporting files and load or run only when needed [9]. This is package anatomy, not an admission policy. Isolated evaluation, staged rollout, operating evidence, and withdrawal still belong to the system around the Skill.

progressive delivery

### 7.4.1 A successful run creates a candidate

Production systems expose the same gap at several scales. Daily trajectories can propose new Skills; bad cases can enter an evaluation set; and large libraries need coexistence tests because a Skill that succeeds alone can still degrade an agent when it competes with dozens of others. In one department, the library had grown to roughly a thousand Skills, with an individual agent loading about a hundred and using thirty to fifty together. These production accounts are documented in the [public record of the ADPS Reflection workshop](https://adpsagent.com/workshops/reflection-2026-08-12/).

trajectory

agent skill

AI agent

That last case changes the meaning of "verified." A successful trace proves that one method worked once under one set of conditions. An isolated benchmark can show that it helps its intended task family. Neither result proves that the Skill will coexist safely with the current library or that the router will send it the right traffic.

Skill extraction should produce a **candidate**. The candidate needs an applicability contract that records:

- the task family and inputs it supports;
- the conditions under which it should and should not be selected;
- required permissions, tools, and dependency versions;
- expected outputs and deterministic checks where available;
- the evidence that led to extraction; and
- a stable logical identity plus a version for the current content.

The stable identity lets the system follow one capability over time. The version changes when its instructions, implementation, contract, or dependencies change. This avoids treating a name and description as proof that two implementations are identical. It also avoids inventing a success rate of 100 percent before the candidate has been tried on a sample. The admission path separates three runtime states, shown in table 7.7.

##### Table 7.7 Skill admission states

| State     | Traffic                   | Evidence held                                             | Next decision                             |
|-----------|---------------------------|-----------------------------------------------------------|-------------------------------------------|
| Candidate | None                      | Source traces, contract, isolated and coexistence results | Revise, reject, or begin trial            |
| Trial     | Bounded and observable    | Passed offline gates plus trial outcomes                  | Activate or return to candidate           |
| Active    | Allowed by routing policy | Complete admission record and operating evidence          | Keep, refine, merge, demote, or deprecate |

The isolated gate evaluates the candidate against the current baseline or general solver. It asks whether the Skill helps the task family in its applicability contract. A benchmark can include correctness, latency, cost, safety, and task-specific properties. A hard regression in one protected dimension stays visible even when a weighted total improves.

isolated gate

The coexistence gate installs the candidate beside the active library. It then checks whether the Skill steals unrelated traffic, conflicts with another Skill, uses incompatible dependencies, expands context or execution cost, or changes an existing task family's result. Passing the isolated gate cannot substitute for this test.

coexistence test

The trial gate gives the candidate bounded traffic after both offline gates pass. Failed trials return the version to candidate status with their evidence attached. The team can revise or reject it without contaminating the active library.

trial gate

##### Figure 7.3 Skill admission and maintenance. A trace proposes a candidate; isolated, coexistence, and trial gates control activation; operating evidence supports refinement, merging, demotion, deprecation, retirement, and rollback.

![Image](7%20Reflection%20and%20evaluation_%20How%20your%20agent%20audits%20and%20learns%20from%20itself%20-%20Designing%20AI%20Agents_images/image_000002_9f903690d29c1eac2a81e6087d314863255fa73d9c5be53fc53887fc731132b6.png)

**Recap 7.4 intro and 7.4.1** to the AI assistant

type

### 7.4.2 One active Skill or conditional coexistence

The admission process does not need a winner-take-all policy. For a simple, stable task family, one active Skill may be easiest to evaluate and route. Functionally duplicate candidates should be merged. Keeping several copies of the same method makes attribution harder and gives the router choices that add no useful flexibility.

winner-take-all policy

agent skill

Complex task families can support several active Skills when their conditions lead to genuinely different choices. Methods may differ because one requires a particular tool version, another costs more but suits higher-risk work, and a third trades completeness for latency on a reversible task. Each active version states those conditions in its applicability contract. Horizontal evaluation can then merge the candidates, activate one, keep them under different conditions, or reject them. A single global score cannot express all four outcomes.

applicability contract

evaluation

### 7.4.3 Route in layers

Library size alone should not determine the routing architecture. A fixed rule that assigns model judgment to a small library and vector search to a large one ignores task risk, description quality, dependency constraints, and the number of plausible matches. Ambiguity can make a small library dangerous, while hard conditions can divide a much larger library cleanly.

routing architecture

similarity search

A production router can make the decision in three layers:

router

1. **Rules exclude.** Permission, risk, dependency, version, and applicability checks remove Skills that are not legal for this task.
2. **Evidence narrows.** Results for the current task family, reliability, cost, and known conflicts reduce the legal set. Missing evidence may reduce the set to zero. evidence
3. **The model interprets context.** The agent may make a semantic choice inside the small legal set and records why it chose that version. AI agent

When one active Skill survives the first two layers, routing is deterministic. When none survives, the agent falls back to the general solver. The router does not force a Skill match merely to increase its hit rate.

**Recap 7.4.2 and 7.4.3** to the AI assistant

type

### 7.4.4 Building Skill Package

The next data model separates the stable capability identity from the current version and keeps evidence beside its state.

##### Listing 7.10 Skill candidate and applicability records

```
from enum import Enum

from typing import Protocol

 

 

class SkillState(str, Enum):

    CANDIDATE = "candidate"

    TRIAL = "trial"

    ACTIVE = "active"

    DEPRECATED = "deprecated"

    RETIRED = "retired"

 

 

@dataclass(frozen=True)

class Applicability:

    task_family: str

    conditions: dict[str, str]

    required_permissions: frozenset[str]

    dependency_spec: dict[str, str]

    max_risk: int

 

 

@dataclass

class SkillVersion:

    skill_id: str

    version: str

    description: str

    instructions: str

    applies: Applicability

    state: SkillState = SkillState.CANDIDATE

    evidence_ids: list[str] = field(default_factory=list)

 

 

@dataclass(frozen=True)

class GateResult:

    passed: bool

    evidence_id: str

    failures: tuple[str, ...] = ()

 

 

class Gate(Protocol):

    def __call__(self, skill: SkillVersion) -> GateResult:

        ...
```

Declares permissions the task must supply before this Skill is eligible.

Creates a candidate; extraction alone does not make it available for use.

The admission function in the next listing requires independent, isolated, coexistence, and trial results. It never asks the model that wrote the Skill to declare its own work verified.

agent skill

##### Listing 7.11 Evidence-backed Skill admission

```
def admit_skill(

    skill: SkillVersion,

    isolated: Gate,

    coexistence: Gate,

    canary: Gate,

) -> bool:

    if skill.state != SkillState.CANDIDATE:

        raise ValueError("admission requires a candidate")

 

    for gate in (isolated, coexistence):

        result = gate(skill)

        if result.evidence_id:

            skill.evidence_ids.append(result.evidence_id)

        if not result.passed or not result.evidence_id:

            return False

 

    skill.state = SkillState.TRIAL

    result = canary(skill)

    if result.evidence_id:

        skill.evidence_ids.append(result.evidence_id)

    if not result.passed or not result.evidence_id:

        skill.state = SkillState.CANDIDATE

        return False

 

    skill.state = SkillState.ACTIVE

    return True
```

Requires both passing results and evidence identifiers before the trial.

Returns a failed trial to candidate status.

Activates the version only after all three gates pass.

A passing gate without a durable evidence identifier is treated as a failed admission decision.

evidence

The hard-filter layer is explicit in listing 7.12. The two injected checks implement environment-specific conditions and dependency compatibility.

hard-filter layer

environment-specific condition

dependency compatibility

##### Listing 7.12 Hard filters for active Skills

```
@dataclass(frozen=True)

class TaskRequest:

    text: str

    family: str

    attributes: dict[str, str]

    risk: int

    permissions: frozenset[str]

    dependencies: dict[str, str]

 

 

def hard_allowed(task, skill, compatible, matches) -> bool:

    applies = skill.applies

    return (

        skill.state == SkillState.ACTIVE

        and task.family == applies.task_family

        and matches(task.attributes, applies.conditions)

        and task.risk <= applies.max_risk

        and applies.required_permissions <= task.permissions

        and compatible(

            task.dependencies,

            applies.dependency_spec,

        )

    )
```

Excludes unadmitted, deprecated, and retired versions before semantic selection.

Checks dependency compatibility as a requirement, not a ranking preference.

The layered router records both the legal set and the evidence shortlist. It checks the narrowing result against the legal set before selection. `narrow` may return an empty list when the available evidence cannot support a selection. `choose` sees only the checked shortlist.

router

evidence shortlist

##### Listing 7.13 Layered Skill routing with abstention

```
def route_skill(

    task,

    skills,

    compatible,

    matches,

    narrow,

    choose,

    record,

):

    legal = [

        skill

        for skill in skills

        if hard_allowed(task, skill, compatible, matches)

    ]

    legal_by_key = {

        (skill.skill_id, skill.version): skill

        for skill in legal

    }

    ranked_keys = [

        (skill.skill_id, skill.version)

        for skill in narrow(task, legal)

    ]

    shortlist = [

        legal_by_key[key]

        for key in dict.fromkeys(ranked_keys)

        if key in legal_by_key

    ]

    if not shortlist:

        record(task, legal, shortlist, None, "general solver")

        return None

 

    if len(shortlist) == 1:

        selected = shortlist[0]

        record(task, legal, shortlist, selected, "one qualified Skill")

        return selected

 

    decision = choose(task, shortlist)

    if decision is None:

        record(task, legal, shortlist, None, "selector abstained")

        return None

    selected_key, reason = decision

    selected = next(

        (

            s

            for s in shortlist

            if (s.skill_id, s.version) == selected_key

        ),

        None,

    )

    if selected is None:

        record(task, legal, shortlist, None, "selector abstained")

        return None

 

    record(task, legal, shortlist, selected, reason)

    return selected
```

A

B

C

**Recap 7.4.4** to the AI assistant

type

### 7.4.5 Maintain the library from operating evidence

An end-of-day hook can collect trajectories. A reflection job can identify a repeated method, dependency change, misroute, or regression and propose a new candidate or revision. The proposal still enters the admission path; the daily job does not promote its own output.

A useful operating record includes the task family and request conditions, every Skill eligible after hard filtering, the selected version and reason, agent and Harness versions, relevant dependencies, outcome, latency, cost, failures, regressions, and later human corrections. Without those fields, the team cannot tell whether a failure came from the agent, the selected Skill, the combination of Skills, or a dependency change.

operating record

hard filtering

AI agent

The processing cadence should follow the rate and risk of change. Daily processing may fit an actively changing coding system. A stable internal workflow may need less frequent analysis. Periodic portfolio review looks for duplicates, uncovered task families, dependency changes, misrouting, conflicts, context cost, and versions that no longer earn their place.

portfolio review

Available actions are `keep`, `refine`, `merge`, `demote`, `deprecate`, and `retire`. Low use sends a Skill to review; it does not justify automatic demotion. A rare incident-response or security Skill may still cover a critical task. Weighted scores can prioritize review, while hard gates control serving. Usage, criticality, coverage, dependency health, and replacement evidence remain separate inputs.

Retirement should be reversible. Automation may withdraw a low-risk Skill when an obsolete dependency, persistent misrouting, a verified replacement, or an explicit policy decision supports the change; regression checks pass; and the previous routing state can be restored. The registry retains the withdrawn version, its evidence, and a rollback reference. Changes affecting safety policy, production boundaries, or several task families still require approval from an authorized person.

retire

The final Skill Package listing asks the trusted registry to validate durable evidence and determine whether the Skill is protected. It validates approval outside the caller when protected scope is involved, then performs withdrawal as one atomic registry change.

agent skill

registry

##### Listing 7.14 Operating evidence and reversible withdrawal

```
@dataclass(frozen=True)

class SkillRunEvidence:

    task_family: str

    legal_versions: tuple[str, ...]

    selected_version: str | None

    agent_version: str

    harness_version: str

    dependencies: dict[str, str]

    outcome: str

    evidence_ids: tuple[str, ...]

 

 

@dataclass(frozen=True)

class WithdrawalEvidence:

    reason: str

    evidence_ids: tuple[str, ...]

    reversible: bool

    rollback_version: str

    approval_id: str | None = None

 

 

def withdraw_skill(

    registry,

    skill,

    evidence,

) -> bool:

    if not evidence.reason or not evidence.evidence_ids:

        return False

    if not registry.valid_evidence(evidence.evidence_ids, skill):

        return False

    if not evidence.reversible:

        return False

    if not registry.has_version(

        skill.skill_id,

        evidence.rollback_version,

    ):

        return False

    protected_scope = registry.is_protected(skill)

    if protected_scope and not registry.valid_approval(

        evidence.approval_id,

        skill,

    ):

        return False

    with registry.atomic_change():

        registry.archive(skill, evidence.rollback_version)

        registry.remove_from_routes(skill.skill_id, skill.version)

        registry.record_withdrawal(skill, evidence)

        skill.state = SkillState.DEPRECATED

    return True
```

Requires a reversible withdrawal with an available rollback version.

Lets the trusted registry determine whether protected scope needs approval.

Archives the version and removes its routing entries in one atomic change.

The pattern earns compound reuse, but its costs also accumulate. Table 7.8 keeps both sides visible.

##### Table 7.8 Skill Package trade-offs

| Advantage                                                    | Limitation                                                         |
|--------------------------------------------------------------|--------------------------------------------------------------------|
| Reusable procedures reduce repeated reasoning and tool work  | Extraction can preserve a one-off workaround as if it were general |
| Applicability contracts make routing and evaluation testable | Contracts and dependencies require continuing maintenance          |
| Conditional coexistence preserves useful specialization      | More active choices increase routing and attribution difficulty    |
| Versioned evidence supports audit, rollback, and retirement  | Library review consumes evaluation and human attention             |

**Recap 7.4.5** to the AI assistant

type

### 7.4.6 When Skill Package breaks

**Premature promotion.** One successful trace becomes reusable production behavior. Keep the result as a candidate until isolated, coexistence, and trial evidence support activation.

premature promotion

**Coexistence regression.** A Skill passes alone but degrades routing, context, or another task family. Evaluate it with the active library and preserve each protected dimension.

coexistence regression

**Routing ambiguity.** Several loosely described Skills match, and the model chooses inconsistently. Add applicability contracts, hard filters, evidence narrowing, and abstention.

routing ambiguity

**Dependency rot.** A formerly useful Skill calls an obsolete tool or follows an old business rule. Track versions, inspect runtime evidence, deprecate reversibly, and retest.

dependency rot

**Portfolio sprawl.** Duplicate and low-value variants increase cost and obscure attribution. Review evidence across runs, then merge, demote, or retire with a rollback record.

portfolio sprawl

rollback record

Admission makes a Skill eligible for routing within its applicability contract. Any tool call or production change produced by that Skill still passes through the Action and Governance controls defined elsewhere in the book. The operating record supports revision or withdrawal. Experience Replay carries advice that can affect judgment without receiving execution authority.

agent skill

applicability contract

experience replay

execution authority

**Recap 7.4.6** to the AI assistant

type

## 7.5 Pattern: Experience Replay

Coding and operations agents expose two different feedback clocks. A coding agent can compile its output, run tests, and inspect a deployment log within minutes. An operations agent may recommend a change whose result appears only after people act on it and the business outcome arrives. Both tasks produce execution traces. The coding task can produce an immediate label; the operations task often cannot.

AI agent

That difference changes how experience should be stored and reused. A trace can be recorded as soon as the run ends. A lesson distilled from that trace still needs evidence. Even an established lesson should enter a later task only when its scope and conditions match. Experience Replay therefore separates three decisions: what to record, what to admit for replay, and what to recall now.

evidence

Experience Replay learns from past execution trajectories and uses a small, relevant part of that history to guide later work. In the two-dimensional framework, it sits at Reflection × Hierarchy. The hierarchy organizes experience by level of abstraction, from complete traces to scoped heuristics. It also keeps raw evidence separate from the advice placed in a live context.

trajectory

heuristic

##### Critical design decision: When may a lesson enter the live context?

**Coordinates:** Reflection × Hierarchy

**Engineering ancestors:** Incident postmortems, case-based reasoning, and experience replay buffers

Use Experience Replay when past outcomes can guide later planning or diagnosis. Separate raw traces, candidate lessons, and replayable heuristics; admit a lesson only with scope, provenance, and evidence; and recall it only when task and trigger conditions match. Keep candidates out of live context, and keep admitted lessons advisory. Measure retrieval, use, decision effect, later outcome, conflict, and context cost.

candidate lesson

Reflexion [10] and ExpeL [11] show how language agents can use stored verbal feedback and experience across later attempts. The production boundary in this section adds admission, scope, version, conflict, and recall decisions around that idea.

##### Figure 7.4 The Experience Replay hierarchy and recall path. Raw traces support candidate lessons; evidence admits scoped heuristics; task and trigger filters decide whether a replayable lesson enters live context.

![Image](7%20Reflection%20and%20evaluation_%20How%20your%20agent%20audits%20and%20learns%20from%20itself%20-%20Designing%20AI%20Agents_images/image_000003_b60af2823cc5c207197e4ea464af1238a05fc5b6d0c7fe7d608c17e64e7e4a48.png)

### 7.5.1 From an execution trace to a replayable lesson

I used to describe this pattern mainly as a memory hierarchy. The harder design question is admission. Presence in the store does not make a lesson true, and truth in one setting does not make it useful in the current one. The hierarchy has three practical levels:

memory hierarchy

- **L0, raw trace.** The complete execution, outcome state, tool evidence, and environment version remain available for audit and analysis. L0 usually stays outside live context. trajectory
- **L1, candidate lesson.** A shorter statement links to one or a few traces and preserves provenance. It is a hypothesis suitable for investigation or a closely bounded retry. candidate lesson
- **L2, replayable heuristic.** A scoped lesson has repeated independent support or a clear causal mechanism backed by external evidence. It may be recalled when task and environment conditions match. heuristic

The transition from L0 to L1 is compression. The transition from L1 to L2 is an evidence decision. Greater abstraction increases the range of possible transfer. Validation determines the range that the system may actually use.

validation

Conflicting experiences should keep the conditions under which each result was observed. Two lessons may recommend different database strategies because they were learned under different data volumes or server versions. A single global winner would erase the distinction that makes both lessons useful. The system can narrow each lesson's applicability, mark the conflict, or return the issue for human analysis.

This admission boundary also separates Experience Replay from Skill Package. The same trace may propose both. Experience admits scoped advice that influences planning, diagnosis, or checks. Skill Package admits a tested procedure that may execute within declared permissions. A replay record carries no execution authority: it cannot by itself authorize a tool call, policy rewrite, or Approval Gate bypass.

experience replay

agent skill

approval gate

**Recap 7.5 intro and 7.5.1** to the AI assistant

type

### 7.5.2 Feedback latency changes the admission test

Feedback latency is the delay between an action and the evidence needed to judge its result. Some tasks close the feedback loop inside one run. Code can compile, a schema can validate, and a test can pass or fail. Other tasks remain open. A recommendation may require a product change, an operational action, or a later response from a user before its value becomes visible.

feedback latency

For immediate feedback, the system can attach the verifier result directly to the trace. The result remains scoped: a passing test establishes what that test checks. It says nothing about effects outside that scope. For delayed feedback, the trace stays pending until the later outcome can be joined to it. A convenient proxy may help with triage, but it should not promote a lesson whose real success criterion has not arrived.

verifier

proxy

Delayed outcomes also complicate attribution. Several decisions may occur between the agent's recommendation and the final result. The replay record should retain the task, versions, intervening actions, and evidence source. When the causal link remains uncertain, the system keeps the lesson as a hypothesis or asks a domain expert to review it. An uncertain outcome should not become a precise confidence score simply because the schema has a field for one.

attribution

AI agent

replay record

### 7.5.3 Record, admit, and recall

The lifecycle is `record -> distill -> validate -> admit -> recall -> observe`. Recording can be broader than admission. Runtime recall is narrower still because every recalled lesson consumes context and may steer a decision.

Recall uses two triggers. Under this policy, a high-risk or known repeated task receives a small preflight recall before planning. A failure, low-confidence state, environment change, or major replan requests targeted recovery recall. Ordinary tasks do not pay the context cost by default. The caller sets the item budget according to task risk and available context.

Hard filters run before semantic matching. They require replayable status, a matching task family, compatible versions, and no unresolved conflict that blocks use. Semantic retrieval sees only the eligible set and may return no result. The system records which lessons were shown, which were used, which decision changed, and which later outcome arrived.

hard filter

**Recap 7.5.2 and 7.5.3** to the AI assistant

type

### 7.5.4 Building Experience Replay

The data model in listing 7.15 keeps raw evidence, candidate lessons, and replayable lessons distinct. It stores versions and conflicts instead of a premature global effectiveness score.

data model

replayable lesson

##### Listing 7.15 Experience records and replay status

```
class ReplayStatus(str, Enum):

    CANDIDATE = "candidate"

    REPLAYABLE = "replayable"

    CONFLICTED = "conflicted"

    RETIRED = "retired"

 

 

@dataclass(frozen=True)

class ExecutionTrace:

    task_id: str

    task: str

    task_family: str

    steps: tuple[dict, ...]

    outcome: str | None

    evidence_ids: tuple[str, ...]

    versions: dict[str, str]

 

 

@dataclass

class Lesson:

    lesson_id: str

    text: str

    source_trace_ids: list[str]

    task_families: set[str]

    independent_cases: int

    causal_mechanism: str | None

    external_evidence_ids: tuple[str, ...]

    status: ReplayStatus = ReplayStatus.CANDIDATE

    version_constraints: dict[str, str] = field(

        default_factory=dict

    )

    unresolved_conflicts: set[str] = field(

        default_factory=set

    )
```

Allows delayed outcomes to remain unknown instead of assuming success.

Keeps a distilled lesson provisional until the admission test passes.

Admission takes the repeated-case rule from a domain policy. A causal path still needs a recorded mechanism, linked external evidence, and a declared task-family scope.

repeated-case rule

##### Listing 7.16 Admitting a scoped lesson for replay

```
def can_admit_lesson(lesson, repeated_case_gate) -> bool:

    repeated = repeated_case_gate(lesson)

    causal = (

        bool(lesson.causal_mechanism)

        and bool(lesson.external_evidence_ids)

    )

    return (

        lesson.status == ReplayStatus.CANDIDATE

        and bool(lesson.source_trace_ids)

        and bool(lesson.task_families)

        and not lesson.unresolved_conflicts

        and (repeated or causal)

    )

 

 

def admit_lesson(lesson, repeated_case_gate) -> bool:

    if not can_admit_lesson(lesson, repeated_case_gate):

        return False

    lesson.status = ReplayStatus.REPLAYABLE

    return True
```

Uses the domain's rule for sufficient repeated-case support.

Accepts repeated support or an evidenced causal mechanism, within the declared scope.

Every route to replayable status therefore retains at least one source trace.

source trace

The trigger policy in listing 7.17 keeps routine tasks free of unsolicited history while allowing preventive and recovery recall.

trigger policy

recovery recall

##### Listing 7.17 Choosing the Experience Replay phase

```
@dataclass(frozen=True)

class RecallContext:

    task_id: str

    task: str

    task_family: str

    versions: dict[str, str]

    high_risk: bool = False

    repeated_task: bool = False

    failed: bool = False

    low_confidence: bool = False

    environment_changed: bool = False

    replanning: bool = False

 

 

def recall_phase(ctx: RecallContext) -> str | None:

    recovery = (

        ctx.failed

        or ctx.low_confidence

        or ctx.environment_changed

        or ctx.replanning

    )

    if recovery: #A

        return "recovery"

    if ctx.high_risk or ctx.repeated_task:

        return "preflight"

    return None #B
```

The retrieval path in listing 7.18 makes task relevance real. The `narrow` function may use embeddings, a model, or a domain classifier, but it receives only lessons with replay authority and valid scope.

##### Listing 7.18 Task-sensitive and trigger-sensitive recall

```
def recall_experience(

    ctx,

    lessons,

    version_check,

    narrow,

    limit,

    record,

):

    if limit <= 0:

        return []

    phase = recall_phase(ctx)

    if phase is None:

        return []

 

    eligible = [ #A

        lesson

        for lesson in lessons

        if lesson.status == ReplayStatus.REPLAYABLE

        and ctx.task_family in lesson.task_families

        and not lesson.unresolved_conflicts

        and version_check(

            lesson.version_constraints,

            ctx.versions,

        )

    ]

    eligible_by_id = {x.lesson_id: x for x in eligible}

    selected = []

    seen = set()

    for item in narrow(ctx, eligible, limit):

        if item.lesson_id not in eligible_by_id: #B

            continue

        if item.lesson_id in seen:

            continue

        selected.append(eligible_by_id[item.lesson_id])

        seen.add(item.lesson_id)

        if len(selected) == limit: #C

            break

    record(

        task_id=ctx.task_id,

        phase=phase,

        eligible_ids=[x.lesson_id for x in eligible],

        selected_ids=[x.lesson_id for x in selected],

    )

    return selected
```

A later outcome must join the recall log. A successful task adds supporting evidence; it does not prove that a recalled lesson caused the success. Keeping retrieval, use, decision effect, and outcome as separate fields prevents correlation from becoming a permanent rule. The pattern's benefits and limits appear together in table 7.9.

recall log

decision effect

##### Table 7.9 Experience Replay trade-offs

| Advantage                                                   | Limitation                                                       |
|-------------------------------------------------------------|------------------------------------------------------------------|
| Raw traces preserve evidence that later analysis may need   | Storing everything does not determine what deserves live context |
| Scoped heuristics can improve future planning and diagnosis | A lesson may overfit the task, version, or environment that      |
|                                                             |    produced it                                                   |
| Triggered recall controls context cost and interference     | A poor trigger can omit useful advice or replay it too late      |
| Provenance and conflict records support revision            | Delayed outcomes make attribution and admission slower           |

**Recap 7.5.4** to the AI assistant

type

### 7.5.5 When Experience Replay breaks

**Candidate leakage.** A freshly distilled lesson enters a live prompt before validation. Keep candidate and replayable stores logically separate, and make the status check part of the retrieval query.

candidate leakage

validation

**Context flooding.** The system retrieves every plausible lesson and leaves the agent to sort them out. Trigger recall only when the task warrants it, apply hard scope filters first, and use a small context budget.

context flooding

AI agent

**Superstitious learning.** The system assigns a result to the most visible action in the trace. Preserve competing explanations and require repeated cases or a causal mechanism with external evidence before cross-task admission.

superstitious learning

evidence

**Stale or conflicting advice.** A sound lesson outlives the dependency or environment in which it was learned. Store version constraints, mark unresolved conflicts, and rerun validation when a relevant environment changes.

stale or conflicting advice

**Authority leakage.** Advisory text is treated as an executable instruction. Keep experience in planning and diagnosis. Tool use, policy change, and production action still pass through Skill, Action, and Governance controls.

authority leakage

governance

The four patterns now have separate objects, time scales, and authority. The next section shows how they can share evidence without becoming one unbounded self-improvement loop.

**Recap 7.5.5** to the AI assistant

type

## 7.6 Composing reflection patterns

The four reflection patterns can share evidence without collapsing into one unbounded loop. During the current task, Generator-Critic revises the artifact, while Self-Heal Loop may change execution steps or bounded state to recover from a failure. Across tasks, Skill Package carries an admitted capability and Experience Replay carries admitted advice. A system may use only the patterns its task and risk justify.

generator-critic loop

fail-diagnose-fix-verify loop

agent skill

experience replay

The composition in figure 7.5 begins with a current task and ends with an accepted result or a handoff. That work produces a trace. Cross-run review may turn the evidence into a Skill candidate, an Experience candidate, both, or neither. Each candidate follows its own admission path before it can affect future work.

skill candidate

experience candidate

##### Figure 7.5 Reflection patterns compose through traces and separate gates. Current-task review and recovery produce evidence; capability admission and replay admission control what later tasks may use.

![Image](7%20Reflection%20and%20evaluation_%20How%20your%20agent%20audits%20and%20learns%20from%20itself%20-%20Designing%20AI%20Agents_images/image_000004_3c59624916d46228f4a6d6a1a923ffd9ce7ccfaf70f0cfe930bd6cd88fa27779.png)

The protected evidence remains outside the writable path. A loop that can rewrite both its behavior and the test used to judge that behavior can manufacture its own success. Tests, policy, gold labels, and production boundaries stay protected unless a separate authorized process approves their revision.

protected evidence

That separation lets reversible, regression-tested changes move automatically while reserving human approval for changes to safety policy, production scope, or several task families.

The composition map in table 7.10 follows one task through the four possible changes.

##### Table 7.10 Composition map for the four reflection patterns

| Pattern           | Trigger                                  | Changed object                                        | Admission or verifier                                            | Effect on later tasks                                         |
|-------------------|------------------------------------------|-------------------------------------------------------|------------------------------------------------------------------|---------------------------------------------------------------|
| Generator-Critic  | Artifact needs review                    | Current artifact version                              | Critic contract and review evidence                              | None unless later cross-run review extracts a candidate       |
| Self-Heal Loop    | Current execution fails                  | Bounded plan, arguments, artifact, or temporary state | Protected verifier, regression, rollback, and handoff            | None unless the repair later enters a separate admission path |
| Skill Package     | Repeatable procedure appears in evidence | Versioned executable capability                       | Isolated, coexistence, and bounded-trial gates                   | Router may select an active Skill within its contract         |
| Experience Replay | Trace suggests a transferable lesson     | Scoped advisory heuristic                             | Independent cases or causal evidence, then task-sensitive recall | Planner or diagnosis may receive a replayable lesson          |

Four design questions keep the composition understandable:

1. **What can the check see?** This is feedback scope. Generator-Critic shows why an artifact check may miss system effects. feedback scope
2. **When does evidence arrive, and how long does the change persist?** These are feedback latency and reflection time scales. Experience Replay carries selected lessons across tasks, sometimes after a delayed outcome. feedback latencyreflection time scale
3. **What may the loop change?** This is modification authority. Self-Heal Loop separates recovery permission from verifier and policy authority. modification authorityrecovery
4. **What evidence is enough to retain the change?** This is evaluation evidence. Skill and Experience admission require more than the trace that proposed them.

These questions also explain the environment-building agent from the opening. Each local check saw the failure in front of it and justified another safeguard. The accumulated cost appeared across runs. The original online loop had authority to add rules, while a wider offline review was needed to merge or retire them.

AI agent

**Recap 7.6 intro** to the AI assistant

type

### 7.6.1 A current-task coordinator

The next listing shows a small coordinator for the current-task half of the composition. It records one trace after review and optional recovery. Cross-run processes may use that trace to propose a Skill or Experience candidate; the coordinator grants neither form of admission. Delivery is accepted only after an accepted review and either successful initial verification or recovered healing that leaves the reviewed artifact unchanged. Unresolved or budget-exhausted review and unrecovered healing are handed off.

trajectory

verification

##### Listing 7.19 Coordinating review, verification, and recovery

```
@dataclass(frozen=True)

class TaskTrace:

    task_id: str

    artifact: str

    review_status: str

    recovery_status: str

    delivery_status: str

    evidence_ids: tuple[str, ...]

 

class ReflectionCoordinator:

    def __init__(self, review, verify, heal, record):

        self.review = review

        self.verify = verify

        self.heal = heal

        self.record = record

 

    def complete(self, task) -> TaskTrace:

        reviewed = self.review(task)

        review_ids = tuple(

            item.evidence_id

            for step in reviewed.history

            for item in step.evidence

        )

        if reviewed.status != "accepted": #A

            trace = TaskTrace(

                task_id=task.task_id,

                artifact=reviewed.artifact,

                review_status=reviewed.status,

                recovery_status="not_started",

                delivery_status="handed_off",

                evidence_ids=review_ids,

            )

            self.record(trace)

            return trace

 

        report = self.verify(reviewed.artifact) #B

        verified = report.passed and not report.regressed

        artifact = reviewed.artifact

        recovery_status = "not_needed"

        recovery_ids = ()

        if not verified:

            healed = self.heal(

                report.failure or "protected_verifier_failed"

            )

            recovery_status = healed["status"]

            if recovery_status == "recovered":

                if "artifact" not in healed:

                    recovery_status = "invalid_recovery_record"

                else:

                    artifact = healed["artifact"]

            recovery_ids = tuple(

                evidence_id

                for attempt in healed["history"]

                for evidence_id in getattr(

                    attempt.get("report"),

                    "evidence_ids",

                    (),

                )

            )

 

        same_version = artifact == reviewed.artifact #C

        deliverable = verified or (

            recovery_status == "recovered" and same_version

        )

        delivery_status = "accepted" if deliverable else "handed_off"

        trace = TaskTrace(

            task_id=task.task_id,

            artifact=artifact,

            review_status=reviewed.status,

            recovery_status=recovery_status,

            delivery_status=delivery_status,

            evidence_ids=(

                review_ids + report.evidence_ids + recovery_ids

            ),

        )

        self.record(trace) #D

        return trace
```

A repaired artifact cannot inherit review status from the version that preceded it. When recovery changes the artifact, the coordinator marks delivery as handed off so Generator-Critic or a wider review flow can review it. Execution or state-only recovery that leaves the reviewed artifact unchanged can complete under the protected verifier.

generator-critic loop

verifier

**Recap 7.6.1** to the AI assistant

type

## 7.7 Evaluation belongs beside the change

Evaluation has already appeared throughout the four patterns. Tests ground the Critic, verifiers and rollback bound Self-Heal, isolated and coexistence checks gate Skills, and delayed outcomes validate Experience. Figure 7.6 and table 7.11 gather those signals in one place. The signals cover different parts of the system, so the stack is not a simple ranking.

evaluation

##### Figure 7.6 The evaluation evidence stack. Structural checks, deterministic verifiers, traces, invariants, semantic review, human evidence, and real outcomes cover progressively different questions and feedback latencies.

![Image](7%20Reflection%20and%20evaluation_%20How%20your%20agent%20audits%20and%20learns%20from%20itself%20-%20Designing%20AI%20Agents_images/image_000005_1170a380d0f07bf47cd6e7d8a1553f9d8bb36bb9dcbe1237642275d4c4bb70b7.png)

Use the cheapest signal that can decide the current question, then add broader signals when the failure can escape its scope. Generator-Critic often combines a semantic rubric with deterministic evidence. Self-Heal requires an external verifier, regression checks, and a rollback result. Skill Package adds isolated evaluation, coexistence evaluation, and a controlled trial. Experience Replay adds task-sensitive recall and the later evidence needed to judge whether the lesson helped.

semantic rubric

fail-diagnose-fix-verify loop

agent skill

isolated evaluation

coexistence test

controlled trial

experience replay

task-sensitive recall

##### Table 7.11 Seven sources of evaluation evidence

| Signal                            | Strongest question                                  | Typical arrival          | Limitation                                                     |
|-----------------------------------|-----------------------------------------------------|--------------------------|----------------------------------------------------------------|
| Structural or schema check        | Is the artifact well formed?                        | Immediate                | Says little about semantic correctness                         |
| Deterministic verifier            | Did the output satisfy an explicit contract?        | Immediate                | Covers only encoded checks                                     |
| Execution trace or reconciliation | Did the expected steps and state changes occur?     | Runtime or shortly after | A plausible path can still pursue the wrong goal               |
| Property or invariant check       | Does behavior preserve a rule across varied inputs? | Runtime or offline       | Cannot test an invariant the team has not specified            |
| Rubric-based model or reviewer    | Does the artifact meet semantic criteria?           | Immediate or batched     | Requires calibrated criteria and an independent review frame   |
| Human sample or expert label      | What did the automated checks miss?                 | Batched                  | Expert attention is scarce and labels require guidance         |
| Real-world outcome                | Did the intervention help in its operating context? | Delayed                  | Other actions and environmental changes complicate attribution |

### 7.7.1 Build and protect the evaluation set

Production traces are useful starting material for an evaluation set. They are candidates, not automatic benchmark entries. The team validates the task and expected outcome, freezes the relevant environment, removes solution hints, and keeps protected evidence hidden from the agent being evaluated. New bad cases can then enter the regression set and follow the same development, evaluation, and promotion path as any other system change.

trajectory

evaluation dataset

AI agent

The evaluation set needs provenance. Record the task source, expected outcome, environment version, labels, review history, and the production failure that motivated the case. Duplicate and contradictory cases need resolution. A benchmark that changes silently cannot support a release decision or a comparison across versions.

provenance

Hard gates should remain visible beside aggregate scores. A weighted total can rise while a safety, latency, or task-family dimension regresses. A hard failure blocks promotion within its scope. Composite scores help compare passing candidates and prioritize investigation; they do not cancel a failed invariant.

hard gate

composite metric

Cost belongs in the same view. A repair that passes after many retries may still degrade the system when token use, elapsed time, state changes, and human intervention are counted. A useful release view pairs effect measures with cost measures. That pairing makes the opening case visible before the build time grows from minutes toward an hour.

The release decision keeps hard gates separate from descriptive scores. An empty evidence set is also a blocked decision.

release decision

##### Listing 7.20 Deciding release from protected evidence

```
@dataclass(frozen=True)

class SignalResult:

    name: str

    passed: bool

    hard_gate: bool

    evidence_id: str

    cost: float

 

 

@dataclass(frozen=True)

class ReleaseDecision:

    allowed: bool

    blocking_signals: tuple[str, ...]

    evidence_ids: tuple[str, ...]

    total_cost: float

 

 

def decide_release(results) -> ReleaseDecision:

    if not results: #A

        return ReleaseDecision(

            allowed=False,

            blocking_signals=("missing_evidence",),

            evidence_ids=(),

            total_cost=0.0,

        )

 

    blockers = tuple(

        result.name

        for result in results

        if result.hard_gate and not result.passed #B

    )

    return ReleaseDecision(

        allowed=not blockers,

        blocking_signals=blockers,

        evidence_ids=tuple(

            result.evidence_id for result in results

        ),

        total_cost=sum(result.cost for result in results),

    )
```

**Recap 7.7 intro and 7.7.1** to the AI assistant

type

## 7.8 Argus checkpoint: Reflection

Argus now has two forms of feedback within the current task and two ways to carry selected learning forward. Generator-Critic compares a current artifact with criteria and evidence. Self-Heal Loop may repair bounded execution when a protected verifier fails. A repeatable procedure becomes a Skill candidate and follows capability admission. A trace or outcome may produce an Experience candidate and follows replay admission.

generator-critic loop

evidence

fail-diagnose-fix-verify loop

skill candidate

trajectory

experience candidate

Before new work, Argus routes only among active Skills. It requests a small set of replayable lessons for selected high-risk or repeated tasks. During recovery, it may recall again after a failure, low-confidence diagnosis, environment change, or major replan. Every route and recall records the legal candidate set, selected version or lesson, reason, and eventual outcome.

agent skill

recovery

The checkpoint in table 7.12 shows what reflection adds to Argus.

##### Table 7.12 Argus reflection checkpoint

| Capability          | Before Chapter 7              | After Chapter 7                                                    |
|---------------------|-------------------------------|--------------------------------------------------------------------|
| Artifact review     | One generated artifact        | Criteria, independent evidence, versioned critique, and bounded    |
|                     |                               |    revision                                                        |
| Failure recovery    | Failure returned to caller    | Policy-bounded diagnosis, atomic repair, protected verification,   |
|                     |                               |    rollback, and handoff                                           |
| Reusable capability | Ad hoc repeated instructions  | Candidate, isolated and coexistence gates, trial, active routing,  |
|                     |                               |    and reversible withdrawal                                       |
| Cross-task advice   | Unfiltered historical context | Trace hierarchy, replay admission, trigger policy, task-sensitive  |
|                     |                               |    recall, and effect logging                                      |
| Evaluation          | Local task result             | Protected multi-signal evidence with hard gates, cost, and delayed |
|                     |                               |    outcomes                                                        |
| Audit and ownership | Fragmented logs               | Linked artifact, repair, Skill, Experience, version, selection,    |
|                     |                               |    and outcome records                                             |

At this checkpoint, Argus still operates within one task context and one evidence chain. Chapter 8 asks what changes when work and evidence are distributed across several participants.

**Recap 7.8** to the AI assistant

type

## 7.9 Summary

- **Reflection connects feedback to a permitted change**. The design specifies what the feedback can see, when the result arrives, what the loop may change, and what evidence is required to retain that change.
- **Generator-Critic** improves a current artifact. Independence comes from a different review frame, criteria, context, or evidence, rather than agent count alone.
- **Self-Heal Loop** has greater recovery authority. It verifies each repair, preserves a rollback path, stops at a bounded limit, and hands control to a person when the recovery boundary is reached.
- **Skill Package** admits executable capability. Promotion requires isolated, coexistence, and trial evidence; routing first filters by permission, risk, dependency, and applicability.
- **Low use sends a Skill to review**. Retirement requires stronger evidence and a reversible path, and consequential scope changes require human approval.
- **Experience Replay** separates raw traces, candidate lessons, and replayable heuristics. Recording, replay admission, and runtime recall are separate decisions.
- **Experience remains advisory**. Recall occurs before planning for selected high-risk or repeated tasks and during recovery after a relevant trigger.
- **Evaluation is part of each pattern's change path**. Deterministic checks, traces, semantic review, invariants, human evidence, and real outcomes cover different scopes and feedback latencies.
- **A hard regression cannot be hidden by an aggregate score**. Cost, latency, state change, and human effort belong alongside task success.
- **Each safeguard in the opening case passed its local check** while the complete system became slower and more conflicted. Cross-run review and explicit retirement authority turn local reflection into system learning.

## 7.10 References

[1] Huang, J., Chen, X., et al. "Large Language Models Cannot Self-Correct Reasoning Yet." ICLR 2024. arXiv:2310.01798.

[2] Pan, L., et al. "Automatically Correcting Large Language Models: Surveying the Landscape of Diverse Automated Correction Strategies." TACL 2024. arXiv:2308.03188.

[3] Gou, Z., et al. "CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing." ICLR 2024. arXiv:2305.11738.

[4] Madaan, A., et al. "Self-Refine: Iterative Refinement with Self-Feedback." NeurIPS 2023. arXiv:2303.17651.

[5] Wataoka, K., Takahashi, T., and Ri, R. "Self-Preference Bias in LLM-as-a-Judge." 2024. arXiv:2410.21819.

evaluator

[6] Zheng, L., et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS 2023. arXiv:2306.05685.

[7] Charas, M., and Bruggmann, M. "Background Coding Agents: Predictable Results Through Strong Feedback Loops (Honk, Part 3)." Spotify Engineering, December 9, 2025. [https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3](https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3).

[8] Wang, G., et al. "Voyager: An Open-Ended Embodied Agent with Large Language Models." TMLR 2024. arXiv:2305.16291.

[9] Anthropic. "Extend Claude with Skills." Claude Code Docs. Accessed August 27, 2026. [https://code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).

[10] Shinn, N., et al. "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023. arXiv:2303.11366.

[11] Zhao, A., et al. "ExpeL: LLM Agents Are Experiential Learners." AAAI 2024. arXiv:2308.10144.
