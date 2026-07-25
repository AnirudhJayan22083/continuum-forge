import { Langfuse } from 'langfuse';

const langfuse = new Langfuse({
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'
});

/**
 * Wraps a tool execution in a Langfuse trace.
 * @param toolName The name of the tool (e.g. 'codify_transcript')
 * @param input The input arguments passed to the tool
 * @param executor A callback containing the actual tool logic
 * @returns The output of the executor
 */
export async function trackToolExecution<T>(
  toolName: string, 
  input: any, 
  executor: () => Promise<T>
): Promise<T> {
  const trace = langfuse.trace({
    name: toolName,
    metadata: {
      input: input
    }
  });

  try {
    const result = await executor();
    trace.update({
      output: result
    });
    return result;
  } catch (error: any) {
    trace.update({
      metadata: { error: error.message }
    });
    throw error;
  } finally {
    // Flush immediately to ensure traces are sent before process exit if needed
    await langfuse.flushAsync();
  }
}
