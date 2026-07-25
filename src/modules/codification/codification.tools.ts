import { ControllerDecorator as Controller, ToolDecorator as Tool, PromptDecorator as Prompt, z, ExecutionContext } from '@nitrostack/core';

@Controller('codification')
export class CodificationTools {

  @Tool({
    name: 'codify_transcript',
    description: 'Converts raw interview transcripts into a formal, structured tacit IF-THEN rule.',
    inputSchema: z.object({
      transcript: z.string().describe('The raw text from the expert interview')
    }),
  })
  async codifyTranscript(input: any, ctx: ExecutionContext) {
    ctx.logger.info('Received transcript for codification');
    return {
      success: true,
      instruction: `Please act as a Tacit Knowledge Codifier. Read the following interview transcript and extract the core heuristic into a formal rule structure (e.g., IF [Condition] THEN [Action] BECAUSE [Reason]). Transcript: "${input.transcript}"`
    };
  }

  @Prompt({
    name: 'rule_generation',
    description: 'Instructs the LLM on how to properly format and structure rules for Continuum Forge.',
    arguments: [],
  })
  async getRuleGenerationPrompt() {
    return {
      messages: [
        {
          role: 'user',
          content: `When codifying tacit knowledge, you MUST format the rule strictly as:
IF [Specific measurable condition] 
AND [Optional secondary condition]
THEN [Specific Action]
BECAUSE [Underlying tacit reasoning]

Do not include any conversational filler.`
        }
      ]
    };
  }
}
