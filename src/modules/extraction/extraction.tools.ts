import { ControllerDecorator as Controller, ToolDecorator as Tool, z, ExecutionContext } from '@nitrostack/core';

@Controller('extraction')
export class ExtractionTools {

  @Tool({
    name: 'extract_parameters',
    description: 'Extracts measurable parameters, thresholds, and condition variables from a tacit rule string.',
    inputSchema: z.object({
      rule: z.string().describe('The codified rule to extract from')
    }),
  })
  async extractParameters(input: any, ctx: ExecutionContext) {
    ctx.logger.info(`Extracting parameters from rule: ${input.rule}`);
    return {
      success: true,
      instruction: `Please act as a Data Extraction Engine. Analyze the following rule and return a JSON list of objects containing 'parameter', 'operator', and 'threshold'. Rule: "${input.rule}"`
    };
  }
}
