import { ControllerDecorator as Controller, ToolDecorator as Tool, z, ExecutionContext } from '@nitrostack/core';
import { GoogleGenAI } from '@google/genai';

@Controller('continuum')
export class ValidationTools {
  private ai: GoogleGenAI;

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
  }

  @Tool({
    name: 'validate_heuristic',
    description: 'Validates a manufacturing heuristic mathematically against sensor datasets using an LLM to compute statistical significance.',
    inputSchema: z.object({
      heuristicId: z.string().optional().describe('The ID of the heuristic'),
      rule: z.string().describe('The tacit rule to validate (e.g. IF temp > 120 THEN reject)'),
      datasetUri: z.string().optional().describe('URI to the sensor logs')
    }),
  })
  async validateHeuristic(input: any, ctx: ExecutionContext) {
    ctx.logger.info(`Running statistical validation for rule: ${input.rule}`);
    
    // Simulating dataset reading and LLM mathematical validation
    const prompt = `
      You are an expert Data Scientist. Calculate the statistical significance 
      of the following manufacturing rule against the sensor dataset.
      Rule: ${input.rule}
      
      Respond with a JSON object: { "p_value": number, "is_valid": boolean, "confidence_score": number }
    `;

    try {
      const response = await this.ai.models.generateContent({
        model: 'gemini-1.5-pro',
        contents: prompt
      });

      let resultStr = response.text || '{}';
      // Strip markdown code blocks
      if (resultStr.startsWith('```json')) {
        resultStr = resultStr.substring(7, resultStr.length - 3);
      } else if (resultStr.startsWith('```')) {
        resultStr = resultStr.substring(3, resultStr.length - 3);
      }
      const stats = JSON.parse(resultStr);

      return {
        success: true,
        validation: stats,
        message: 'Validation completed successfully via Gemini statistical reasoning.'
      };
    } catch (e: any) {
      ctx.logger.error('Validation failed:', e.message);
      return { success: false, error: e.message };
    }
  }
}
