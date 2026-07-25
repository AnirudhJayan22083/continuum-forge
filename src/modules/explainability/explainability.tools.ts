import { ControllerDecorator as Controller, ToolDecorator as Tool, z, ExecutionContext } from '@nitrostack/core';

@Controller('explainability')
export class ExplainabilityTools {

  @Tool({
    name: 'generate_explanation',
    description: 'Generates human-readable reasoning for why a specific heuristic or rule passed or failed validation.',
    inputSchema: z.object({
      rule: z.string().describe('The rule being explained'),
      validationResult: z.boolean().describe('Whether the rule passed or failed statistical validation')
    }),
  })
  async generateExplanation(input: any, ctx: ExecutionContext) {
    ctx.logger.info(`Explaining validation result for rule: ${input.rule}`);
    return {
      success: true,
      instruction: `Please act as an Explainable AI for Manufacturing. The rule "${input.rule}" resulted in a validation status of "${input.validationResult ? 'Passed' : 'Failed'}". Please write a concise, human-readable explanation of why this likely occurred, suitable for a factory floor operator.`
    };
  }
}
