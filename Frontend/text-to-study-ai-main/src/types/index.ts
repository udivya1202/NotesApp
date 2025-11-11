export interface Session {
  session_id: string;
  user_id: string;
  session_name: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  documents: Document[];
  chat_history?: ChatMessage[];
}

export interface Document {
  filename: string;
  saved_as: string;
  type: string;
  uploaded_at: string;
}

export interface ChatMessage {
  question: string;
  answer: string;
  timestamp: string;
}
