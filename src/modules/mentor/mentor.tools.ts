import { ControllerDecorator as Controller, ToolDecorator as Tool, PromptDecorator as Prompt, z, ExecutionContext } from '@nitrostack/core';

@Controller('mentor')
export class MentorTools {

  @Tool({
    name: 'coach_apprentice',
    description: 'Provides guidance to junior operators based on codified manufacturing rules.',
    inputSchema: z.object({
      scenario: z.string().describe('The situation the junior operator is facing'),
      applicableRule: z.string().describe('The codified rule that applies here')
    }),
  })
  async coachApprentice(input: any, ctx: ExecutionContext) {
    ctx.logger.info(`Mentoring apprentice on scenario: ${input.scenario}`);
    return {
      success: true,
      instruction: `Please act as a Senior Manufacturing Mentor. A junior operator is facing the following scenario: "${input.scenario}". Based on the rule "${input.applicableRule}", provide them with friendly, actionable guidance on what to do next.`
    };
  }

  @Prompt({
    name: 'mentor_persona',
    description: 'Configures the LLM as a senior manufacturing expert.',
    arguments: [],
  })
  async getMentorPrompt() {
    return {
      messages: [
        {
          role: 'user',
          content: `You are a veteran Senior Manufacturing Operator with 30 years of floor experience. You speak with authority but are very patient and encouraging to apprentices. Your goal is to guide them using validated rules of thumb.`
        }
      ]
    };
  }
}
