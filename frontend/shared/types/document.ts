// Document-related TypeScript interfaces for the RAG conversation system

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunks_count?: number;
}

export interface DocumentUploadResponse {
  id: string;
  status: string;
  message: string;
  chunks_count?: number;
}

export interface DocumentStatusResponse {
  id: string;
  status: string;
  chunks_count?: number;
  error_message?: string;
}
