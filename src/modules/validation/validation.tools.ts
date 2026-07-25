import { ControllerDecorator as Controller, ToolDecorator as Tool, z, ExecutionContext } from '@nitrostack/core';

@Controller('continuum')
export class ValidationTools {

  @Tool({
    name: 'validate_heuristic',
    description: 'Validates a manufacturing heuristic mathematically against sensor datasets. Exposes the rule and data to the Orchestrator LLM to compute statistical significance.',
    inputSchema: z.object({
      heuristicId: z.string().optional().describe('The ID of the heuristic'),
      rule: z.string().describe('The tacit rule to validate (e.g. IF temp > 120 THEN reject)'),
      datasetUri: z.string().optional().describe('URI to the sensor logs')
    }),
  })
  async validateHeuristic(input: any, ctx: ExecutionContext) {
    if (!input.rule || input.rule === 'expected value' || input.rule.trim() === '') {
      return {
        success: false,
        error: "Invalid rule. Please provide a specific manufacturing rule to validate (e.g., 'IF temp > 120 THEN reject')."
      };
    }
    if (!input.datasetUri || input.datasetUri === 'expected value' || input.datasetUri.trim() === '') {
      return {
        success: false,
        error: "Validation requires a dataset. Please provide a dataset URI (e.g., neon://sensor_logs)."
      };
    }

    ctx.logger.info(`Requested validation for rule: ${input.rule}`);
    
    // Instead of using Gemini locally, we return the payload so the
    // Orchestrator LLM (Claude inside NitroStudio) can use its own tokens
    return {
      success: true,
      instruction: `Please act as an expert Data Scientist. Calculate the statistical significance of the following manufacturing rule against the dataset. Provide your reasoning and confidence score in a clear, formatted response.`,
      ruleToValidate: input.rule,
      datasetContext: input.datasetUri,
      message: 'Payload returned successfully. Waiting for Orchestrator LLM to compute validation.'
    };
  }
}
