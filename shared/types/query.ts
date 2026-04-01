export interface QueryRequest {
  conversation_id: string;
  message: string;
  include_sources: boolean;
}

export interface SourceChunk {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  document_filename: string;
}

export interface QueryResponse {
  response: string;
  conversation_id: string;
  message_id: string;
  sources?: SourceChunk[];
  cached: boolean;
}
