/**
 * Chat streaming service for SSE-based chat completion
 * Connects to backend /chat/complete endpoint with stream=true
 */

export interface ChatStreamMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatStreamRequest {
  messages: ChatStreamMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream: boolean;
}

export interface ChatStreamChunk {
  id?: string;
  object?: string;
  created?: number;
  model?: string;
  choices?: Array<{
    index: number;
    delta: {
      role?: string;
      content?: string;
    };
    finish_reason?: string | null;
  }>;
}

export interface ChatStreamCallbacks {
  onChunk?: (content: string) => void;
  onComplete?: (fullContent: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Stream chat completion from backend using Server-Sent Events (SSE)
 */
export async function streamChatCompletion(
  request: ChatStreamRequest,
  callbacks: ChatStreamCallbacks
): Promise<void> {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = `${baseURL}/chat/complete`;

  let fullContent = '';
  let controller: AbortController | null = null;

  try {
    controller = new AbortController();
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        
        // Skip empty lines and comments
        if (!trimmed || trimmed.startsWith(':')) {
          continue;
        }

        // Parse SSE format: "data: {...}"
        if (trimmed.startsWith('data: ')) {
          const data = trimmed.substring(6);
          
          // Check for stream end marker
          if (data === '[DONE]') {
            break;
          }

          try {
            const chunk: ChatStreamChunk = JSON.parse(data);
            
            // Extract content from chunk
            if (chunk.choices && chunk.choices.length > 0) {
              const delta = chunk.choices[0].delta;
              if (delta.content) {
                fullContent += delta.content;
                callbacks.onChunk?.(delta.content);
              }
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE chunk:', data, parseError);
          }
        }
      }
    }

    // Notify completion
    callbacks.onComplete?.(fullContent);

  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    callbacks.onError?.(err);
    throw err;
  } finally {
    controller?.abort();
  }
}

/**
 * Non-streaming chat completion for fallback
 */
export async function chatCompletion(
  request: Omit<ChatStreamRequest, 'stream'>
): Promise<string> {
  const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = `${baseURL}/chat/complete`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ...request, stream: false }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }

  const data = await response.json();
  
  // Extract content from OpenAI-format response
  if (data.choices && data.choices.length > 0) {
    return data.choices[0].message?.content || '';
  }

  throw new Error('Unexpected response format');
}
