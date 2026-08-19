# workflow_agents

A film-pitch factory. One conversational agent takes an idea from the user, then hands it to
a pipeline that researches, drafts, critiques, revises, and finally writes a pitch document
to disk.

It exists to show the three ADK workflow primitives working together in one graph:
**Sequential** (fixed order), **Loop** (repeat until satisfied), and **Parallel**
(fan out, join).

## The hierarchy

```mermaid
flowchart TD
    user(["User"]) --> intake

    subgraph greeter["greeter · root_agent"]
        direction TB

        intake["greeter's own turn<br/>captures the idea"]

        subgraph team["film_concept_team"]
            direction TB

            subgraph room["writers_room · 5 passes"]
                direction TB
                researcher["researcher<br/>looks it up on Wikipedia"]
                screenwriter["screenwriter<br/>logline + three-act outline"]
                critic["critic<br/>approve, or send back"]
                researcher --> screenwriter --> critic
            end

            subgraph pre["preproduction_team"]
                direction TB
                box["box_office_researcher"]
                cast["casting_agent"]
            end

            writer["file_writer<br/>saves the pitch document"]
        end

        intake ==>|"transfer_to_agent"| team
    end

    critic -.->|"not there yet"| researcher
    room -->|"exit_loop"| pre
    pre --> writer

    classDef leaf fill:#ffffff,stroke:#d2d2d7,stroke-width:1.5px,color:#1d1d1f
    classDef entry fill:#f5f5f7,stroke:#86868b,stroke-width:1.5px,color:#1d1d1f
    class intake,researcher,screenwriter,critic,box,cast,writer leaf
    class user entry

    style greeter fill:#ffffff,stroke:#1d1d1f,stroke-width:2px,color:#1d1d1f,stroke-dasharray: 6 4
    style team fill:#f5f9ff,stroke:#0071e3,stroke-width:1.5px,color:#1d1d1f
    style room fill:#fff9f0,stroke:#ff9f0a,stroke-width:1.5px,color:#1d1d1f
    style pre fill:#f2fbf5,stroke:#34c759,stroke-width:1.5px,color:#1d1d1f
```

| | Orchestrator | Runs its children |
| --- | --- | --- |
| 🟦 | `SequentialAgent` | one after another, in order |
| 🟧 | `LoopAgent` | over and over, until `exit_loop` or the cap |
| 🟩 | `ParallelAgent` | all at once, then joins |
| ⬛ | `LlmAgent` with `sub_agents` | **dashed** — the model decides when to hand off via `transfer_to_agent`, and control does not come back |

## What runs when

| # | Agent | Type | Does |
| --- | --- | --- | --- |
| 1 | `greeter` | **LlmAgent — `root_agent`** | Asks the user for a historical figure, stores the answer, then hands off |
| 2 | `researcher` | LlmAgent | Wikipedia lookup for facts to write from |
| 3 | `screenwriter` | LlmAgent | Writes a logline and three-act outline |
| 4 | `critic` | LlmAgent | Reviews it — calls `exit_loop` when it is good enough |
| — | | | Steps 2–4 repeat, up to five passes |
| 5 | `box_office_researcher` | LlmAgent | Estimates commercial potential — runs with 6 |
| 6 | `casting_agent` | LlmAgent | Suggests actors — runs with 5 |
| 7 | `file_writer` | LlmAgent | Assembles everything and writes the file |

## How the state moves

Agents never call each other directly. They read and write keys on shared session state,
which is what lets the loop accumulate work across passes.

```mermaid
flowchart TD
    greeter["greeter · root_agent"] --> k1(["PROMPT"])
    k1 --> researcher["researcher"] --> k2(["research"])
    k2 --> screenwriter["screenwriter"] --> k3(["PLOT_OUTLINE"])
    k3 --> critic["critic"] --> k4(["CRITICAL_FEEDBACK"])
    k4 -.-> screenwriter

    k3 --> box["box_office_researcher"] --> k5(["box_office_report"])
    k3 --> cast["casting_agent"] --> k6(["casting_report"])

    k3 --> writer["file_writer"]
    k5 --> writer
    k6 --> writer
    writer --> doc[["pitch document"]]

    classDef agent fill:#ffffff,stroke:#d2d2d7,stroke-width:1.5px,color:#1d1d1f
    classDef state fill:#f5f5f7,stroke:#c7c7cc,stroke-width:1px,color:#6e6e73
    classDef out fill:#f5f9ff,stroke:#0071e3,stroke-width:1.5px,color:#1d1d1f
    class greeter,researcher,screenwriter,critic,box,cast,writer agent
    class k1,k2,k3,k4,k5,k6 state
    class doc out
```

| Key | Written by | Read by |
| --- | --- | --- |
| `PROMPT` | `greeter` | `researcher`, `screenwriter` |
| `research` | `researcher` | `screenwriter`, `critic` |
| `PLOT_OUTLINE` | `screenwriter` | everyone downstream |
| `CRITICAL_FEEDBACK` | `critic` | `researcher`, `screenwriter` |
| `box_office_report` | `box_office_researcher` | `file_writer` |
| `casting_report` | `casting_agent` | `file_writer` |

`PROMPT`, `research`, `PLOT_OUTLINE` and `CRITICAL_FEEDBACK` are appended to rather than
overwritten, so each loop pass sees every earlier draft and critique. `box_office_report`
and `casting_report` use `output_key`, so each is replaced with the agent's latest answer.

## Tools

| Tool | Used by | Purpose |
| --- | --- | --- |
| `append_to_state` | greeter, researcher, screenwriter, critic | Append a value to a state key |
| `wikipedia` | researcher | LangChain's Wikipedia tool, wrapped by `LangchainTool` |
| `exit_loop` | critic | Ends `writers_room` early once the outline is good |
| `write_file` | file_writer | Writes the finished pitch to disk |

## Running it

```bash
make run-agent AGENT=workflow_agents   # terminal
make run-web                           # browser, then pick workflow_agents
```

Give it a historical figure — `albert einstein` works well. Expect several model calls per
loop pass, so a full run is not instant.

> **Note:** the Wikipedia tool needs a descriptive User-Agent — Wikimedia rejects the
> `wikipedia` package's default with a 403, which surfaces as
> `Expecting value: line 1 column 1 (char 0)`. `agent.py` sets one at import; keep it if you
> copy this tool elsewhere.

See [AGENTS.md](../../AGENTS.md) for setup, credentials, and troubleshooting.
