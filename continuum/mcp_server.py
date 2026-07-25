from mcp.server.fastmcp import FastMCP
from continuum.agents.validation import ValidationEngine
from continuum.models.heuristic import Heuristic
import json
import os

# Create the FastMCP server instance
mcp = FastMCP("Continuum_MCP_Server")

# Initialize the validation engine with our datasets
# Assuming this script is run from the project root
SENSOR_DATA_PATH = "continuum/data/sensor_history.csv"
LOGS_DATA_PATH = "continuum/data/maintenance_logs.csv"

# Make sure the paths exist before initializing, or we can lazy-load
engine = None
def get_engine():
    global engine
    if engine is None:
        engine = ValidationEngine(SENSOR_DATA_PATH, LOGS_DATA_PATH)
    return engine

@mcp.tool()
def validate_technician_heuristic(machine: str, component: str, failure_mode: str, trigger: str, conditions: list[str]) -> str:
    """
    Validates a technician's tacit knowledge (heuristic) against historical maintenance and sensor data.
    
    Args:
        machine: The machine ID (e.g., 'MACH-A'). Use 'ALL' for general rules.
        component: The component that fails (e.g., 'Bearing').
        failure_mode: The type of failure (e.g., 'Bearing Failure').
        trigger: The core underlying trigger description.
        conditions: A list of mathematical conditions to test, using variables 'humidity_percent' and 'vibration_mm_s' (e.g., ['humidity_percent > 80', 'vibration_mm_s > 3.0']).
    
    Returns:
        A JSON string containing the statistical validation results, including p-value, chi-square, and explanation.
    """
    try:
        engine = get_engine()
        
        # Create a heuristic object
        heuristic = Heuristic(
            machine=machine,
            component=component,
            failure=failure_mode,
            trigger=trigger,
            conditions=conditions,
            symptoms=[], # Not strictly required for the math validation
            recommended_action="N/A",
            expert_confidence=0.5
        )
        
        # Run validation
        result = engine.validate(heuristic)
        
        # Return structured JSON result to the LLM
        return json.dumps({
            "accepted": result.accepted,
            "support_count": result.support_count,
            "conditional_probability": result.conditional_probability,
            "pearson_correlation": result.pearson_correlation,
            "chi_square_stat": result.chi_square_stat,
            "p_value": result.p_value,
            "explanation": result.explanation
        }, indent=4)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    # Start the MCP server using stdio transport (standard for local MCP clients like Nitrochat CLI)
    print("Starting Continuum MCP Server...")
    mcp.run(transport='stdio')
