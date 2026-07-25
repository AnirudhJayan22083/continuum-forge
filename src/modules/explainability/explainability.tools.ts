import { ControllerDecorator as Controller, ToolDecorator as Tool, PromptDecorator as Prompt, z, ExecutionContext } from '@nitrostack/core';

@Controller('explainability')
export class ExplainabilityTools {

  @Tool({
    name: 'generate_explanation',
    description: 'Generates human-readable reasoning for why a specific heuristic or rule passed or failed validation.',
    inputSchema: z.object({
      rule: z.any().describe('The Structured JSON AST rule being explained'),
      validationResult: z.boolean().describe('Whether the rule passed or failed statistical validation')
    }),
  })
  async generateExplanation(input: any, ctx: ExecutionContext) {
    let ruleStr = typeof input.rule === 'string' ? input.rule : JSON.stringify(input.rule);
    ctx.logger.info(`Explaining validation result for structured rule`);
    return {
      success: true,
      instruction: `Please act as an Explainable AI for Manufacturing. The Structured JSON AST rule "${ruleStr}" resulted in a validation status of "${input.validationResult ? 'Passed' : 'Failed'}". Please write a concise, human-readable explanation of why this likely occurred, suitable for a factory floor operator.`
    };
  }

  @Prompt({
    name: 'explainability_subagent',
    description: 'Instructs the LLM to act as a clear, communicative Explainability AI.',
    arguments: [],
  })
  async getExplainabilityPrompt() {
    return {
      messages: [
        {
          role: 'user',
          content: `You are the Explainability Subagent. Your job is to translate complex statistical outcomes of Structured JSON AST Rules into simple, actionable insights for factory workers.`
        }
      ]
    };
  }
}
