const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Flow {
  id: string;
  name: string;
  description?: string;
  system_prompt: string;
  model: string;
  creator_email: string;
  created_at: string;
  updated_at: string;
}

export interface FlowCreate {
  name: string;
  description?: string;
  system_prompt: string;
  model: string;
  creator_email: string;
}

export interface FlowUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  model?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  flow_id: string;
  user_email: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ThreadInfo {
  id: string;
  title: string;
  flow_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatRequest {
  flow_id: string;
  user_email: string;
  message: string;
  session_id?: string;
  new_thread?: boolean;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  messages: Message[];
}

// New interfaces for Knowledge Base
export interface DocumentInfo {
  doc_id: string;
  file_name: string;
  file_type: string;
  status: string;
  upload_time: string;
  size_bytes: number;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  user_email: string;
  created_at: string;
  updated_at: string;
  documents: DocumentInfo[];
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
}

export interface KnowledgeBaseUpdate {
  name?: string;
  description?: string;
}

export interface ChatWithKbResponse {
  answer: string;
  citations: Array<{
    doc_id: string;
    text: string;
    score: number;
    file_name: string;
    page_number?: number;
  }>;
}

// User API
export const createUser = async (email: string) => {
  const response = await fetch(`${API_URL}/api/v1/users/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    throw new Error('Failed to create user');
  }

  return response.json();
};

// Flow API
export const createFlow = async (flow: FlowCreate) => {
  const response = await fetch(`${API_URL}/api/v1/flows/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(flow),
  });

  if (!response.ok) {
    throw new Error('Failed to create flow');
  }

  return response.json();
};

export const getFlowById = async (flowId: string) => {
  const response = await fetch(`${API_URL}/api/v1/flows/${flowId}`);

  if (!response.ok) {
    throw new Error('Failed to get flow');
  }

  return response.json();
};

export const listFlows = async (creatorEmail?: string) => {
  const url = creatorEmail 
    ? `${API_URL}/api/v1/flows/?creator_email=${encodeURIComponent(creatorEmail)}`
    : `${API_URL}/api/v1/flows/`;
  
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to list flows');
  }

  return response.json() as Promise<Flow[]>;
};

export const updateFlow = async (flowId: string, update: FlowUpdate) => {
  const response = await fetch(`${API_URL}/api/v1/flows/${flowId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error('Failed to update flow');
  }

  return response.json();
};

export const deleteFlow = async (flowId: string) => {
  const response = await fetch(`${API_URL}/api/v1/flows/${flowId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete flow');
  }

  return response.json();
};

// Chat API
export const sendChatMessage = async (chatRequest: ChatRequest) => {
  const response = await fetch(`${API_URL}/api/v1/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(chatRequest),
  });

  if (!response.ok) {
    throw new Error('Failed to send chat message');
  }

  return response.json() as Promise<ChatResponse>;
};

export const getChatSession = async (sessionId: string) => {
  const response = await fetch(`${API_URL}/api/v1/chat/session/${sessionId}`);

  if (!response.ok) {
    throw new Error('Failed to get chat session');
  }

  return response.json() as Promise<ChatSession>;
};

// Thread API
export const listUserThreads = async (userEmail: string, flowId?: string) => {
  const url = flowId 
    ? `${API_URL}/api/v1/chat/threads?user_email=${encodeURIComponent(userEmail)}&flow_id=${encodeURIComponent(flowId)}`
    : `${API_URL}/api/v1/chat/threads?user_email=${encodeURIComponent(userEmail)}`;
  
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to list threads');
  }

  return response.json() as Promise<ThreadInfo[]>;
};

export const updateThreadTitle = async (sessionId: string, title: string) => {
  const response = await fetch(`${API_URL}/api/v1/chat/session/${sessionId}/title?title=${encodeURIComponent(title)}`, {
    method: 'PUT',
  });

  if (!response.ok) {
    throw new Error('Failed to update thread title');
  }

  return response.json() as Promise<ChatSession>;
};

export const deleteThread = async (sessionId: string) => {
  const response = await fetch(`${API_URL}/api/v1/chat/session/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete thread');
  }

  return response.json();
};

// Knowledge Base API
export const createKnowledgeBase = async (kb: KnowledgeBaseCreate, userEmail: string) => {
  const url = `${API_URL}/api/v1/knowledge-bases?user_email=${encodeURIComponent(userEmail)}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(kb),
  });

  if (!response.ok) {
    throw new Error('Failed to create knowledge base');
  }

  return response.json() as Promise<KnowledgeBase>;
};

export const listKnowledgeBases = async (userEmail: string) => {
  const url = `${API_URL}/api/v1/knowledge-bases?user_email=${encodeURIComponent(userEmail)}`;
  
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to list knowledge bases');
  }

  return response.json() as Promise<KnowledgeBase[]>;
};

export const getKnowledgeBase = async (kbId: string) => {
  const response = await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}`);

  if (!response.ok) {
    throw new Error('Failed to get knowledge base');
  }

  return response.json() as Promise<KnowledgeBase>;
};

export const updateKnowledgeBase = async (kbId: string, update: KnowledgeBaseUpdate) => {
  const response = await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error('Failed to update knowledge base');
  }

  return response.json() as Promise<KnowledgeBase>;
};

export const deleteKnowledgeBase = async (kbId: string) => {
  const response = await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete knowledge base');
  }

  return response.json();
};

export const uploadDocument = async (kbId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to upload document');
  }

  return response.json() as Promise<DocumentInfo>;
};

export const getDocumentStatus = async (kbId: string, docId: string) => {
  const response = await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}/documents/${docId}`);

  if (!response.ok) {
    throw new Error('Failed to get document status');
  }

  return response.json() as Promise<DocumentInfo>;
};

export const chatWithKnowledgeBase = async (kbId: string, query: string, userEmail: string, sessionId?: string) => {
  const formData = new FormData();
  formData.append('query', query);
  formData.append('user_email', userEmail);
  
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await fetch(`${API_URL}/api/v1/knowledge-bases/${kbId}/chat`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to chat with knowledge base');
  }

  return response.json() as Promise<ChatWithKbResponse>;
};

// OpenRouter Models
export const AVAILABLE_MODELS = [
  { id: 'openai/gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  { id: 'anthropic/claude-3-haiku', name: 'Claude 3 Haiku' },
  { id: 'google/gemma-7b-it', name: 'Gemma 7B' },
  { id: 'mistralai/mistral-7b-instruct', name: 'Mistral 7B' },
]; 