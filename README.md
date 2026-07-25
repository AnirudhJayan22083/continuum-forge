# CONTINUUM — Tacit Knowledge Capture & Transfer Network

**Purpose:** Capture manufacturing tacit knowledge from experienced technicians before retirement.

**Core Innovation:** Every extracted heuristic is statistically validated against historical maintenance and sensor data before becoming operational knowledge.

## Quick Start

```bash
cd continuum
pip install -r requirements.txt
python -m continuum.main init
python -m continuum.main demo
```

## Commands

- `continuum init` — Initialize database and load synthetic data
- `continuum interview` — Conduct grounded interview with technician
- `continuum extract` — Extract structured heuristics from transcript
- `continuum validate` — Validate heuristic against historical data
- `continuum explain` — Generate evidence and natural-language explanation
- `continuum codify` — Store validated rule in operational database
- `continuum mentor` — Get real-time recommendation from validated rules
- `continuum demo` — Execute complete pipeline end-to-end

## Architecture

**Clean Architecture** — Business logic separated from CLI layer.

```
continuum/
├── agents/              # AI agents (elicitation, extraction, validation, etc.)
├── services/            # Business logic layer
├── cli/                 # Typer CLI commands
├── models/              # Pydantic data models
├── database/            # SQLite schema and initialization
├── utils/               # Logging and utilities
├── data/                # Synthetic datasets and outputs
├── config/              # Configuration (interview queue)
└── tests/               # Unit tests
```

## Key Features

### Phase 1: Foundation & Synthetic Data
- SQLite database schema
- Pydantic models for employees, maintenance logs, heuristics, validation results
- Synthetic datasets with embedded statistical patterns
- Interview queue ordered by experience and retirement date

### Phase 2: Elicitation Agent
- Grounded interview generation using Claude API
- Intelligent follow-up questions
- Transcript storage

### Phase 3: Knowledge Extraction Agent
- Structured heuristic extraction from transcripts
- JSON schema with machine, component, failure, trigger, conditions, symptoms, recommended action

### Phase 4: Validation Engine (Core)
- Statistical validation using Pandas, NumPy, SciPy
- Support count, conditional probability, Pearson correlation, chi-square p-value
- Confidence scoring and decision (Accepted/Rejected)
- Unit tests

### Phase 5: Explainability Engine
- Natural-language explanations
- Supporting historical incidents
- Matplotlib charts saved to disk
- CLI output explaining acceptance/rejection

### Phase 6: Codification Agent
- Convert accepted heuristics to operational rules
- SQLite storage with duplicate detection
- Static SVG/matplotlib diagram generation

### Phase 7: Mentor Agent
- Real-time sensor event processing
- Rule matching and recommendation
- Confidence scoring and supporting evidence

## Synthetic Data

The system includes synthetic datasets with:
- **3 machines** (Machine-A, Machine-B, Machine-C)
- **3 technicians** with varying experience levels
- **3 interview transcripts** grounded in real incidents
- **Historical maintenance logs** (2026-01-01 to 2026-07-25)
- **Sensor history** with embedded patterns
- **1 real pattern**: Humidity > 80% AND Increasing vibration → Bearing Failure (30+ positive, 60+ negative occurrences)
- **1 false pattern**: Failures increase every Tuesday (fails statistical validation)

## Testing

```bash
pytest tests/ -v --cov=continuum
```

## Development

No external HTTP layer. All output renders via Rich CLI or is saved to disk (matplotlib charts).

---

**Built for a 24-hour hackathon. Focused, modular, demonstrable.**
