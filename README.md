# Continuum Forge

**Tacit Knowledge Capture, Codification & Transfer Engine for Manufacturing Industry 4.0**  
Built with NitroStack MCP Framework, Neon PostgreSQL Telemetry, and Langfuse Observability.

---

## Executive Summary & Problem Statement

In industrial manufacturing, over 80% of critical operational rules of thumb reside exclusively in the heads of senior technicians. When a veteran technician retires or leaves a shift, decades of unwritten safety knowledge and equipment diagnostics are lost.

Continuum Forge solves this industry bottleneck by using an Agentic Model Context Protocol (MCP) Pipeline that:
1. Elicits unwritten tacit knowledge through interview transcripts.
2. Codifies human heuristics into machine-readable Structured JSON AST (Abstract Syntax Tree) Rules.
3. Validates rules statistically against real-time and historical Neon PostgreSQL sensor telemetry.
4. Delivers real-time coaching to junior operators with dynamic verbosity settings (`short` for immediate emergency fixes vs `detailed` for training).
5. Tracks every tool call in Langfuse for enterprise-grade transparency and zero AI hallucination.

---

## System Architecture

```mermaid
flowchart TD
    A[Senior Tech / Lead Operator] -->|Interview Transcript| B[Codification Module]
    B -->|Structured JSON AST| C[Parameter Extraction Engine]
    C -->|Extracted Thresholds| D[Neon PostgreSQL Sensor Telemetry]
    D -->|Historical Validation| E[Statistical Validation Engine]
    E -->|Confidence & Significance| F[Explainability Engine]
    F -->|Verified Rule Registry| G[Mentor Persona Module]
    G -->|Real-Time Guidance| H[Junior Operator / Industrial Web UI]

    subgraph Telemetry & Observability
        B -.->|Telemetry Span| L[Langfuse Observability]
        D -.->|Telemetry Span| L
        E -.->|Telemetry Span| L
        G -.->|Telemetry Span| L
    end
```

---

## Key Features & Architectural Innovations

### 1. Structured JSON AST Rule Codification
Human heuristics like "When vibration is over 4.5 mm/s and temperature is above 90C, shut it down to prevent a fire" are converted into deterministic JSON ASTs:
```json
{
  "operator": "AND",
  "conditions": [
    { "parameter": "vibration (mm/s)", "operator": ">", "threshold": 4.5 },
    { "parameter": "temperature (C)", "operator": ">", "threshold": 90 }
  ],
  "action": "SHUTDOWN"
}
```

### 2. Live Neon PostgreSQL Sensor Validation
Queries historical machine telemetry (`sensor readings` table on `MACHINE B`) to verify whether rule conditions ever triggered simultaneously in historical logs.

### 3. Flexible Verbosity Mode (Short vs Detailed)
- `verbosity: "short"`: Provides strictly the immediate emergency action (`ACTIVATE EMERGENCY SHUTDOWN PUMP B IMMEDIATELY`).
- `verbosity: "detailed"`: Provides a full senior mentor coaching session explaining root cause and preventive measures.

### 4. End-to-End Telemetry with Langfuse
Every MCP tool execution is wrapped with `trackToolExecution()`. Input parameters, database query rows, validation outputs, and execution latencies are logged in real-time to Langfuse Cloud.

### 5. Interactive Web Dashboard & Rendered MCP Widgets
Includes a standalone Web Dashboard (`http://localhost:3001`) with:
- Rule AST Visualizer Widget
- Mentor Guidance Card Widget
- Database Table Visualizer Widget

---

## Installation & Environment Setup

### Prerequisites
- Node.js: v18.x or v20.x
- npm: v9.x or higher
- NitroStack CLI: Installed globally (`npm install -g @nitrostack/cli`)

### Environment Variables Setup
Create a `.env` file in the root directory:

```env
# Server Mode & Port
NODE_ENV=production
PORT=3000

# LLM Providers (Provide at least one)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Neon PostgreSQL Database
DATABASE_URL=postgres://user:password@ep-sample-pooler.neon.tech/neondb?sslmode=require

# Langfuse Observability Telemetry
LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_BASE_URL=https://jp.cloud.langfuse.com
```

### Local Installation

```bash
# 1. Clone the repository
git clone https://github.com/AadiHaldar/continuum-forge.git
cd continuum-forge

# 2. Install dependencies
npm install

# 3. Build the application & MCP widgets
npm run build

# 4. Start the production server
npm start
```

---

## Usage & Running the Master Orchestrator Pipeline

### Running via NitroChat / NitroStudio
Connect your MCP client to:
- Streamable MCP HTTP Endpoint: `http://localhost:3000/mcp`
- Legacy SSE Endpoint: `http://localhost:3000/sse`

### Sample Test Prompt (Pump B Motor Burnout Scenario)

> "Run the master orchestrator pipeline for the Pump B motor burnout scenario. The lead tech's rule is: 'When vibration is over 4.5 mm/s and temperature is above 90C, shutdown immediately.' Validate this against the database.
>
> A junior tech just reported seeing 5.0 mm/s and 95C right now. I am in a huge rush—skip the detailed explanation and use your short verbosity setting to give me just the immediate fix."

---

## Documentation Index

Detailed documentation files are available in the `docs/` directory:
- [Demo Script](docs/demo-script.md) — 3-minute video presentation transcript and breakdown
- [Submission Checklist](docs/submission-checklist.md) — Platform verification and cloud deployment audit
- [Verification Guide](docs/verification.md) — System health check and validation procedures
