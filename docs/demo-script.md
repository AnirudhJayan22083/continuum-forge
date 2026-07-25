# Official 3-Minute Demo Video Script & Screen Walkthrough

Project: Continuum Forge — Tacit Knowledge Capture, Codification & Transfer Engine  
Team: Soumith's LLM Abusers  
Target Duration: Exactly 3:00 Minutes (180 Seconds)  
Format: Screen Recording with Live Voiceover Narration

---

## Second-by-Second Video Map

| Time | Segment Name | What to Show on Screen | Voiceover Narration Script |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:30** | **Problem Statement** | GitHub README or slide showing industrial plant crisis diagram | *"In industrial manufacturing, over 80% of critical operational knowledge lives only in the heads of senior technicians. When a lead tech retires or leaves a shift, decades of unwritten diagnostic rules are lost, leading to catastrophic equipment burnouts and dangerous plant fires."* |
| **0:30 - 1:00** | **NitroStudio App Canvas** | Open NitroStudio App Canvas showing 6 MCP tools connected to NitroStack Agent | *"Meet Continuum Forge, built on the NitroStack MCP Framework. Our system operates a 7-step pipeline that ingests raw interview transcripts, codifies them into Structured JSON AST rules, and validates them statistically against real-time Neon PostgreSQL sensor telemetry."* |
| **1:00 - 2:00** | **Live Working Demo** | NitroChat Web UI (`nitrochat-con-...nitrocloud.ai/embed`). Run Pump B scenario prompt. | *"Let's see it in action. A junior tech reports 5.0 mm/s vibration and 95°C temperature on Pump B. Watch as the Master Orchestrator codifies the lead tech's rule, queries 20 Neon DB sensor rows, and renders our interactive Emergency Guidance Card instructing 'ACTIVATE EMERGENCY SHUTDOWN IMMEDIATELY'."* |
| **2:00 - 2:30** | **Langfuse Observability** | Langfuse Cloud Dashboard (`jp.cloud.langfuse.com`) showing real-time tool execution spans | *"To ensure zero AI hallucination, every single tool call is tracked in Langfuse Cloud. Here in our telemetry waterfall, we can inspect the exact SQL queries executed against Neon DB, parameter extractions, and execution latencies in real-time."* |
| **2:30 - 3:00** | **Deployment & Wrap-Up** | NitroStack Cloud Dashboard showing LIVE status & GitHub repository | *"Continuum Forge is actively deployed on NitroStack Cloud and open-sourced on GitHub. It bridges the generational skill gap, turning fragile human experience into resilient industrial safety. Thank you!"* |

---

## Detailed Step-by-Step Recording Instructions

### Segment 1: Problem Statement (0:00 - 0:30)
- **What to open on screen:** Start recording with `https://github.com/AnirudhJayan22083/continuum-forge` open in your web browser. Scroll down to the System Architecture diagram.
- **Action:** Mouse hover over the senior technician input box and Neon DB telemetry nodes.
- **Speaker script:**
  > "Hello everyone. Today, manufacturing plants face a massive crisis: tacit knowledge loss. Over 80% of critical operational rules of thumb reside exclusively in the minds of senior technicians. When a lead tech retires, their unwritten expertise vanishes—leading to costly motor burnouts and plant fires."

---

### Segment 2: System Architecture & NitroStudio Canvas (0:30 - 1:00)
- **What to open on screen:** Switch tab to **NitroStudio App Canvas** (`docs/screenshots/nitrostudio-app-canvas.png` or live NitroStudio app).
- **Action:** Highlight the 6 MCP tools (`codify_transcript`, `extract_parameters`, `query_neon_database`, `validate_heuristic`, `generate_explanation`, `coach_apprentice`).
- **Speaker script:**
  > "To solve this, we built Continuum Forge using the NitroStack MCP Framework. Continuum Forge operates an end-to-end tacit knowledge pipeline. It ingests interview transcripts, codifies them into Structured JSON AST rules, validates them statistically against Neon PostgreSQL sensor telemetry, and coaches junior technicians in real time."

---

### Segment 3: Live Demo in NitroChat (1:00 - 2:00)
- **What to open on screen:** Open Hosted NitroChat Web UI (`https://nitrochat-con-soumiths-llm-abusers-amrita-university-coimbatore.app.nitrocloud.ai/embed`).
- **Action:** Paste this exact prompt into NitroChat:
  > `"Run the master orchestrator pipeline for the Pump B motor burnout scenario. The lead tech's rule is: 'When vibration is over 4.5 mm/s and temperature is above 90C, shutdown immediately.' Validate this against the database.`
  > 
  > `A junior tech just reported seeing 5.0 mm/s and 95C right now. Use short verbosity setting to give me just the immediate fix."`
- **What happens on screen:** NitroChat streams back the response, codifying the AST rule, querying 20 Neon DB sensor rows, and displaying the **Emergency Guidance Card** instructing `ACTIVATE EMERGENCY SHUTDOWN IMMEDIATELY`.
- **Speaker script:**
  > "Let's look at a live demonstration. A junior tech reports 5.0 mm/s vibration and 95°C temperature on Pump B right now. We send this to our Master Orchestrator with short verbosity mode. 
  > 
  > Notice how NitroStack automatically codifies the rule, queries 20 historical Neon DB sensor readings, and renders our Emergency Guidance Card instructing the operator: 'ACTIVATE EMERGENCY SHUTDOWN IMMEDIATELY', skipping unnecessary fluff when seconds count."

---

### Segment 4: Langfuse Observability & Telemetry (2:00 - 2:30)
- **What to open on screen:** Switch tab to **Langfuse Cloud Dashboard** (`https://jp.cloud.langfuse.com`).
- **Action:** Click on the top trace span (`coach_apprentice`) to expand the waterfall view showing input SQL queries and JSON output payloads.
- **Speaker script:**
  > "How do we know the AI didn't hallucinate this? 
  > 
  > Switching to our Langfuse Observability Dashboard, we see a complete waterfall trace of the execution. We can inspect the exact SQL query executed against our Neon PostgreSQL database, returned sensor rows, and parameters. Everything is 100% deterministic, transparent, and auditable."

---

### Segment 5: Cloud Deployment & Closing (2:30 - 3:00)
- **What to open on screen:** Switch tab to NitroStack Cloud Dashboard showing **continuum forge** status `● Live MCP`.
- **Speaker script:**
  > "Continuum Forge is actively deployed on NitroStack Cloud and open-sourced on GitHub. It turns fragile human experience into resilient, automated industrial safety. Thank you!"
