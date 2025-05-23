"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Flow, Message, ThreadInfo, deleteThread, getChatSession, getFlowById, listFlows, listUserThreads, sendChatMessage, updateThreadTitle } from "@/lib/api";
import { getUserEmail, isAuthenticated } from "@/lib/auth";

export default function ChatPage() {
  const [selectedFlow, setSelectedFlow] = useState<Flow | null>(null);
  const [availableFlows, setAvailableFlows] = useState<Flow[]>([]);
  const [threads, setThreads] = useState<ThreadInfo[]>([]);
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const [showThreads, setShowThreads] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [threadTitle, setThreadTitle] = useState("");
  const [editingTitle, setEditingTitle] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingFlows, setLoadingFlows] = useState(true);
  const [error, setError] = useState("");
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const flowIdFromUrl = searchParams.get('flow');
  const threadIdFromUrl = searchParams.get('thread');

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load available flows
  useEffect(() => {
    const fetchFlows = async () => {
      try {
        if (!isAuthenticated()) {
          router.push('/');
          return;
        }
        
        const flows = await listFlows();
        setAvailableFlows(flows);
        
        // If flow ID is in URL, select that flow
        if (flowIdFromUrl) {
          const selectedFlow = await getFlowById(flowIdFromUrl);
          setSelectedFlow(selectedFlow);

          // Load threads for this flow
          const userEmail = getUserEmail();
          if (userEmail) {
            const threadsData = await listUserThreads(userEmail, flowIdFromUrl);
            setThreads(threadsData);

            // If thread ID is in URL, load that thread
            if (threadIdFromUrl) {
              setSelectedThread(threadIdFromUrl);
              const session = await getChatSession(threadIdFromUrl);
              setMessages(session.messages);
              setThreadTitle(session.title);
            }
          }
        }
      } catch (err) {
        console.error(err);
        setError('Failed to load flows');
      } finally {
        setLoadingFlows(false);
      }
    };
    
    fetchFlows();
  }, [flowIdFromUrl, threadIdFromUrl, router]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus title input when editing
  useEffect(() => {
    if (editingTitle && titleInputRef.current) {
      titleInputRef.current.focus();
    }
  }, [editingTitle]);

  // Handle flow selection
  const handleFlowSelect = async (flowId: string) => {
    try {
      const flow = await getFlowById(flowId);
      setSelectedFlow(flow);
      setMessages([]);
      setSelectedThread(null);
      setThreadTitle("");
      
      // Load threads for this flow
      const userEmail = getUserEmail();
      if (userEmail) {
        const threadsData = await listUserThreads(userEmail, flowId);
        setThreads(threadsData);
      }
      
      // Update URL
      router.push(`/chat?flow=${flowId}`);
      
      // Show thread selection
      setShowThreads(true);
    } catch (err) {
      console.error(err);
      setError('Failed to select flow');
    }
  };

  // Handle thread selection
  const handleThreadSelect = async (threadId: string) => {
    try {
      if (!selectedFlow) return;
      
      const session = await getChatSession(threadId);
      setMessages(session.messages);
      setSelectedThread(threadId);
      setThreadTitle(session.title);
      
      // Update URL
      router.push(`/chat?flow=${selectedFlow.id}&thread=${threadId}`);
      
      // Hide thread selection
      setShowThreads(false);
    } catch (err) {
      console.error(err);
      setError('Failed to load thread');
    }
  };

  // Handle new thread creation
  const handleNewThread = () => {
    setMessages([]);
    setSelectedThread(null);
    setThreadTitle("New Chat");
    setShowThreads(false);
    
    // Update URL to remove thread parameter
    if (selectedFlow) {
      router.push(`/chat?flow=${selectedFlow.id}`);
    }
  };

  // Handle title update
  const handleTitleUpdate = async () => {
    if (!selectedThread || !threadTitle.trim()) return;
    
    try {
      await updateThreadTitle(selectedThread, threadTitle);
      setEditingTitle(false);
      
      // Refresh threads list
      if (selectedFlow) {
        const userEmail = getUserEmail();
        if (userEmail) {
          const threadsData = await listUserThreads(userEmail, selectedFlow.id);
          setThreads(threadsData);
        }
      }
    } catch (err) {
      console.error(err);
      setError('Failed to update thread title');
    }
  };

  // Handle delete thread
  const handleDeleteThread = async (threadId: string, event: React.MouseEvent) => {
    // Stop propagation to prevent thread selection
    event.stopPropagation();
    
    // Confirm deletion
    if (!confirm("Are you sure you want to delete this thread? This action cannot be undone.")) {
      return;
    }
    
    try {
      await deleteThread(threadId);
      
      // If we're deleting the currently selected thread
      if (selectedThread === threadId) {
        setSelectedThread(null);
        setMessages([]);
        setThreadTitle("");
        
        // Update URL
        if (selectedFlow) {
          router.push(`/chat?flow=${selectedFlow.id}`);
        }
      }
      
      // Refresh thread list
      if (selectedFlow) {
        const userEmail = getUserEmail();
        if (userEmail) {
          const threadsData = await listUserThreads(userEmail, selectedFlow.id);
          setThreads(threadsData);
        }
      }
    } catch (err) {
      console.error(err);
      setError('Failed to delete thread');
    }
  };

  // Handle message submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !selectedFlow) return;
    
    const userEmail = getUserEmail();
    if (!userEmail) {
      router.push('/');
      return;
    }
    
    // Add user message to UI immediately
    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setMessage("");
    setLoading(true);
    
    try {
      // Send message to API
      const response = await sendChatMessage({
        flow_id: selectedFlow.id,
        user_email: userEmail,
        message: userMessage.content,
        session_id: selectedThread || undefined,
        new_thread: !selectedThread
      });
      
      // Update messages and session ID
      setMessages(response.messages);
      
      if (!selectedThread) {
        setSelectedThread(response.session_id);
        
        // Refresh threads list
        const threadsData = await listUserThreads(userEmail, selectedFlow.id);
        setThreads(threadsData);
        
        // Get thread title
        const session = await getChatSession(response.session_id);
        setThreadTitle(session.title);
        
        // Update URL
        router.push(`/chat?flow=${selectedFlow.id}&thread=${response.session_id}`);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  if (loadingFlows) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Loading...
        </h1>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {!selectedFlow ? (
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
            Select a Flow to Chat With
          </h1>
          
          {availableFlows.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg p-6 text-center">
              <p className="text-gray-600 dark:text-gray-400">No flows available.</p>
              <Link 
                href="/flows/new"
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                Create a flow
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {availableFlows.map(flow => (
                <div 
                  key={flow.id} 
                  className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg cursor-pointer"
                  onClick={() => handleFlowSelect(flow.id)}
                >
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      {flow.name}
                    </h3>
                    {flow.description && (
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        {flow.description}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : showThreads ? (
        // Thread selection screen
        <div>
          <div className="mb-6">
            <button
              onClick={() => {
                setSelectedFlow(null);
                setShowThreads(false);
                router.push('/chat');
              }}
              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            >
              &larr; Back to flows
            </button>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Chats with {selectedFlow.name}
            </h1>
          </div>
          
          <div className="mb-6">
            <button
              onClick={handleNewThread}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              New Chat
            </button>
          </div>

          {threads.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg p-6 text-center">
              <p className="text-gray-600 dark:text-gray-400">No conversations yet.</p>
              <button
                onClick={handleNewThread}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                Start a new chat
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {threads.map(thread => (
                <div 
                  key={thread.id} 
                  className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 relative"
                  onClick={() => handleThreadSelect(thread.id)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {thread.title}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {thread.message_count} {thread.message_count === 1 ? 'message' : 'messages'} · 
                        {' '}{new Date(thread.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteThread(thread.id, e)}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 p-1"
                      aria-label="Delete thread"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        // Chat interface
        <div className="flex flex-col h-[calc(100vh-10rem)]">
          <div className="flex justify-between items-center mb-4">
            <div>
              <button
                onClick={() => {
                  setShowThreads(true);
                  router.push(`/chat?flow=${selectedFlow.id}`);
                }}
                className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                &larr; Back to chats
              </button>
              
              <div className="flex items-center">
                {editingTitle ? (
                  <div className="flex mt-2">
                    <input
                      ref={titleInputRef}
                      type="text"
                      value={threadTitle}
                      onChange={(e) => setThreadTitle(e.target.value)}
                      className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleTitleUpdate();
                        }
                      }}
                    />
                    <button
                      onClick={handleTitleUpdate}
                      className="ml-2 px-3 py-1 bg-blue-600 text-white rounded-md"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingTitle(false)}
                      className="ml-2 px-3 py-1 bg-gray-500 text-white rounded-md"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <h1 className="text-2xl font-semibold text-gray-900 dark:text-white flex items-center">
                    {threadTitle || "New Chat"}
                    {selectedThread && (
                      <button
                        onClick={() => setEditingTitle(true)}
                        className="ml-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                      >
                        ✏️
                      </button>
                    )}
                  </h1>
                )}
              </div>
              
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Flow: {selectedFlow.name}
              </p>
            </div>
            
            <button
              onClick={handleNewThread}
              className="px-3 py-1 border border-transparent rounded-md shadow-sm text-xs font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              New Chat
            </button>
          </div>
          
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border-l-4 border-red-500 p-4 mb-4">
              <p className="text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}
          
          <div className="flex-grow bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg mb-4 overflow-y-auto">
            <div className="p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center py-10">
                  <p className="text-gray-500 dark:text-gray-400">
                    Start a conversation with this flow.
                  </p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div 
                    key={index}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div 
                      className={`max-w-[75%] px-4 py-2 rounded-lg ${
                        msg.role === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={loading}
              placeholder="Type your message..."
              className="flex-grow px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
            <button
              type="submit"
              disabled={loading || !message.trim()}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
} 