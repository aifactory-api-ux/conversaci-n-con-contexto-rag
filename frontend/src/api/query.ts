import { QueryRequest, QueryResponse } from '../../shared/types/query';

export async function sendQuery(queryRequest: QueryRequest, token: string): Promise<QueryResponse> {
  // Minimal stub: returns a fake QueryResponse
  return {
    message_id: 'stub-message-id',
    conversation_id: queryRequest.conversation_id,
    response: 'Stub response',
    sources: [],
    cached: false
  };
}
