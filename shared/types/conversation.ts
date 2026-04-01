export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  started_at: string;
  last_activity: string;
  status: 'active' | 'archived';
}

export interface ConversationCreate {
  title: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: string;
}
