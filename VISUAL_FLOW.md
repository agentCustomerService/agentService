# Visual Flow Diagrams

## 1. Complete Request-Response Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │  POST /chat                   │
            │  {message, order_id}          │
            └──────────────┬────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────────┐
            │  FastAPI Endpoint (/chat)                │
            │  - Create or get session                 │
            │  - Initialize agent state                │
            └──────────────┬───────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────────┐
            │  invoke agent (LangGraph)                │
            │  graph.ainvoke(state)                    │
            └──────────────┬───────────────────────────┘
                           │
                ┌──────────┴──────────┬─────────────┐
                │                     │             │
                ▼                     ▼             ▼
        ┌─────────────┐      ┌──────────────┐  ┌─────────────┐
        │  analyze()  │─────→│pending_      │──│ save_agent_ │
        │             │      │ actions: []  │  │ result()    │
        │ LLM checks  │      │              │  │             │
        │ message     │      │user_confir   │  │SaveDB:      │
        │             │      │med: False    │  │- session    │
        └─────────────┘      │              │  │- state      │
                             │response: ""  │  │- history    │
                             └──────────────┘  └─────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
         ┌──────────────────┐        ┌───────────────────┐
         │ should_display   │        │ Return Response   │
         │_actions()        │        │ awaiting_confirm  │
         │ Has actions?     │        │ation: true        │
         └─────┬──────┬─────┘        │                   │
               │ YES  │ NO           │pending_actions: []│
               │      │              │executed_actions:[]│
               ▼      └─────────────→│                   │
         ┌──────────────────┐        └───────────────────┘
         │  display_        │                │
         │  actions()       │                │
         │                  │                │
         │Log pending       │                │
         │actions           │                │
         └─────┬────────────┘                │
               │                            │
               ▼                            ▼
         ┌──────────────────┐        ┌─────────────────────┐
         │ WAIT FOR USER    │        │ HTTP Response       │
         │ CONFIRMATION     │        │ 200 OK              │
         │                  │        │ {                   │
         │ Show actions     │        │   success: true,    │
         │ pending_actions: │        │   session_id: "...",│
         │ ["cancel",       │        │   pending_actions:[]│
         │  "refund"]       │        │   awaiting_confirm  │
         └──────────────────┘        │   ation: false      │
               │                      │ }                   │
               └──────────────────────→────────────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │  CLIENT RECEIVES RESPONSE    │
                        │  AND SHOWS TO USER           │
                        └──────────────┬───────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────────┐
                        │  USER DECISION               │
                        │  Confirm or Cancel?          │
                        └─────────┬──────────┬─────────┘
                                  │          │
                        ┌─────────┘          └──────────┐
                        │                                │
                        ▼                                ▼
            ┌─────────────────────┐        ┌──────────────────┐
            │ POST /actions/      │        │ POST /actions/   │
            │ confirm             │        │ confirm          │
            │ {confirmed: true}   │        │ {confirmed:false}│
            └──────────┬──────────┘        └────────┬─────────┘
                       │                           │
                ┌──────┴─────────┐         ┌───────┴────────┐
                │                │         │                │
                ▼                ▼         ▼                ▼
        ┌────────────────┐ ┌────────────────────────────────┐
        │ execute() node │ │ DISCARD pending_actions        │
        │ - Run cancel   │ │ Log: "User cancelled"          │
        │ - Run refund   │ │ Return: executed_actions: []   │
        │ - Update logs  │ │ response: "No actions..."      │
        └────────┬───────┘ └────────────┬───────────────────┘
                 │                      │
                 ▼                      ▼
        ┌────────────────────────────────────────┐
        │ generate_response()                    │
        │ Create summary of actions taken        │
        └────────┬─────────────────────────────┘
                 │
                 ▼
        ┌────────────────────────────────────────┐
        │ Return HTTP Response                   │
        │ {                                      │
        │   executed_actions: ["cancel","refund"]│
        │   response: "Completed actions..."     │
        │   logs: [...]                          │
        │ }                                      │
        └────────┬─────────────────────────────┘
                 │
                 ▼
        ┌────────────────────────────────────────┐
        │ CLIENT RECEIVES FINAL RESULT           │
        │ Shows user the outcome                 │
        └────────────────────────────────────────┘
```

## 2. LangGraph State Nodes

```
                    ┌─────────────────────┐
                    │      START          │
                    └──────────┬──────────┘
                               │
                               ▼
        ┌──────────────────────────────────────┐
        │      analyze()                       │
        │  ┌────────────────────────────────┐ │
        │  │ Input State:                   │ │
        │  │ - session_id                   │ │
        │  │ - message                      │ │
        │  │ - order_id                     │ │
        │  │ - actions: []                  │ │
        │  │ - pending_actions: []          │ │
        │  │ - user_confirmed: false        │ │
        │  │                                │ │
        │  │ Task: LLM analyzes message    │ │
        │  │                                │ │
        │  │ Output State:                  │ │
        │  │ - actions: ["cancel","refund"]│ │
        │  │ - pending_actions: same       │ │
        │  │ - user_confirmed: false       │ │
        │  └────────────────────────────────┘ │
        └────────────┬─────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────┐
        │  should_display_actions()            │
        │  (Conditional Edge / Router)         │
        │                                      │
        │  if state.pending_actions:           │
        │    → route to "display_actions"      │
        │  else:                               │
        │    → route to "generate_response"    │
        └───┬────────────────────────────┬─────┘
            │ YES (has pending)          │ NO (no pending)
            ▼                            ▼
    ┌───────────────────────┐  ┌─────────────────────────┐
    │  display_actions()    │  │  generate_response()    │
    │  ┌─────────────────┐  │  │  ┌───────────────────┐  │
    │  │ Input:          │  │  │  │ Input:            │  │
    │  │ pending_actions │  │  │  │ executed_actions[]│  │
    │  │ logs: [...]     │  │  │  │                   │  │
    │  │                 │  │  │  │ Task: Create      │  │
    │  │ Task: Log       │  │  │  │ response summary  │  │
    │  │ pending actions │  │  │  │                   │  │
    │  │ for review      │  │  │  │ Output:           │  │
    │  │                 │  │  │  │ response: "No..." │  │
    │  │ Output:         │  │  │  └───────────────────┘  │
    │  │ logs updated    │  │  │          │               │
    │  │ pending_actions │  │  │          │               │
    │  │ (unchanged)     │  │  │          │               │
    │  └─────────────────┘  │  │          │               │
    └───┬────────────────────┘  │          │               │
        │                       │          │               │
        ▼                       │          │               │
    ┌──────────────────────┐   │          │               │
    │  execute()           │   │          │               │
    │  ┌────────────────┐  │   │          │               │
    │  │ Input:         │  │   │          │               │
    │  │ actions: ["..."]   │   │          │               │
    │  │ user_confirmed:    │   │          │               │
    │  │  (from /confirm)   │   │          │               │
    │  │                │  │   │          │               │
    │  │ If user_confir │  │   │          │               │
    │  │ med==True:     │  │   │          │               │
    │  │ - Execute      │  │   │          │               │
    │  │   cancel       │  │   │          │               │
    │  │ - Execute      │  │   │          │               │
    │  │   refund       │  │   │          │               │
    │  │ - Log results  │  │   │          │               │
    │  │                │  │   │          │               │
    │  │ Output:        │  │   │          │               │
    │  │ executed_      │  │   │          │               │
    │  │ actions:       │  │   │          │               │
    │  │ ["cancel",     │  │   │          │               │
    │  │  "refund"]     │  │   │          │               │
    │  │ logs: updated  │  │   │          │               │
    │  └────────────────┘  │   │          │               │
    └────┬─────────────────┘   │          │               │
         │                     │          │               │
         ▼                     │          │               │
    ┌──────────────────────┐   │          │               │
    │ should_continue()    │   │          │               │
    │ (Conditional Edge)   │   │          │               │
    │                      │   │          │               │
    │ if more actions:     │   │          │               │
    │   → execute (loop)   │───┘          │               │
    │ else:               │              │               │
    │   → generate_resp   │──────────────┘               │
    └────┬─────────┬──────┘                              │
         │ LOOP    │ DONE                               │
         └─────────┴────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────────┐
        │      END                             │
        └──────────────────────────────────────┘
```

## 3. State Lifecycle

```
REQUEST LIFECYCLE
═════════════════════════════════════════════════════════════════

TIME: T0 - Initial Request
┌────────────────────────────────────────────────────────────┐
│ AgentState {                                               │
│   session_id: "550e8400...",                              │
│   message: "cancel my order",                             │
│   order_id: "ORD-12345",                                  │
│   actions: [],                                            │
│   pending_actions: [],                                    │
│   executed_actions: [],                                   │
│   user_confirmed: false,                                  │
│   logs: [],                                               │
│   response: ""                                            │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
                      ▼ (analyze node)
TIME: T1 - After LLM Analysis
┌────────────────────────────────────────────────────────────┐
│ AgentState {                                               │
│   ...same...                                              │
│   actions: ["cancel"],                                    │
│   pending_actions: ["cancel"],    ← IDENTIFIED            │
│   executed_actions: [],                                   │
│   user_confirmed: false,                                  │
│   logs: []                                                │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
              ▼ (display_actions node)
TIME: T2 - Actions Displayed to User
┌────────────────────────────────────────────────────────────┐
│ AgentState {                                               │
│   ...same...                                              │
│   logs: [                                                 │
│     "Pending actions to execute: cancel"                 │
│   ],                                                      │
│   response: "No actions were performed."    ← WAITING    │
│ }                                                          │
│                                                            │
│ ⚠️  SYSTEM WAITS FOR USER CONFIRMATION                    │
│     POST /actions/confirm {confirmed: true/false}         │
└────────────────────────────────────────────────────────────┘
              ▼ (user confirms: confirmed=true)
TIME: T3 - Execute Node (only if confirmed)
┌────────────────────────────────────────────────────────────┐
│ AgentState {                                               │
│   ...same...                                              │
│   actions: [],                          ← EXECUTED        │
│   pending_actions: [],                                    │
│   executed_actions: ["cancel"],         ← RESULTS         │
│   user_confirmed: true,                 ← CONFIRMED       │
│   logs: [                                                 │
│     "Pending actions to execute: cancel",                │
│     "Order ORD-12345 canceled"                           │
│   ]                                                       │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
          ▼ (generate_response node)
TIME: T4 - Final Response
┌────────────────────────────────────────────────────────────┐
│ AgentState {                                               │
│   ...same...                                              │
│   response: "Completed actions: cancel"  ← SUMMARY        │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
              ▼
        RETURN TO CLIENT
```

## 4. User Decision Points

```
                    User Sends Message
                           │
                           ▼
                    LLM Identifies Actions
                           │
                    ┌──────┴─────────┐
                    │                │
              ACTIONS        NO ACTIONS
              FOUND          FOUND
                │                │
                ▼                ▼
        DISPLAY TO USER    RETURN RESPONSE
        pending_actions    awaiting_confirmation
        awaiting_confirm     = false
        ation = true         NO USER ACTION
                │              NEEDED
                ▼
        USER MUST DECIDE
        ┌────────────────────┐
        │ CONFIRM (true)     │ or │ CANCEL (false)
        └────────────────────┘
                │                     │
                ▼                     ▼
        POST /actions/confirm  POST /actions/confirm
        {confirmed: true}      {confirmed: false}
                │                     │
                ▼                     ▼
        EXECUTE              DISCARD
        ACTIONS              ACTIONS
                │                     │
                ▼                     ▼
        Return Results      Return Empty
        executed_actions[]  executed_actions[]
```

## 5. Database Persistence

```
┌──────────────────────────────────────┐
│      Database (SQLite)               │
│      agent_state.db                  │
└──────────────────────────────────────┘
              │
        ┌─────┼─────┬──────────┐
        │     │     │          │
        ▼     ▼     ▼          ▼
    ┌────┐ ┌────┐ ┌────┐ ┌─────────────┐
    │ SE-│ │INT-│ │STATE    │ INTERAC-   │
    │SSI-│ │ERA-│ │HISTORY  │ TIONS      │
    │ONS │ │CTI-│ │         │            │
    │    │ │ONS │ │         │            │
    └────┘ └────┘ └────┘ └─────────────┘
      │      │      │           │
      │      │      │           │
    S_id   Msg   State       Actions
    Created Img  Snapshot     Taken
    At      Order Actions    Results
    Updated SnpshResp Logs
     Meta   Logs  Saved
      data

FLOW: agent execution → save_agent_result() → database
      retrieve data ← get_session() ← /actions/confirm endpoint
```

These diagrams show:

1. **Complete HTTP flow** from request to response
2. **Node transitions** in the LangGraph
3. **State changes** through execution lifecycle
4. **User decision points** and their outcomes
5. **Database persistence** of session data
