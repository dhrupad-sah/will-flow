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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600 mb-4"></div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Loading...
          </h1>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {!selectedFlow ? (
        <div className="space-y-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-500 to-purple-600 text-transparent bg-clip-text mb-6">
            Select a Flow to Chat With
          </h1>
          
          {availableFlows.length === 0 ? (
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm shadow-lg rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
              <div className="mb-6">
                <div className="inline-block p-3 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-6 text-lg">No flows available.</p>
              <Link 
                href="/flows/new"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all"
              >
                Create a flow
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {availableFlows.map(flow => (
                <div 
                  key={flow.id} 
                  className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm shadow-lg rounded-xl overflow-hidden cursor-pointer border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all hover:scale-[1.02] group"
                  onClick={() => handleFlowSelect(flow.id)}
                >
                  <div className="h-2 bg-gradient-to-r from-indigo-500 to-purple-600"></div>
                  <div className="px-6 py-5 sm:p-6">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {flow.name}
                    </h3>
                    {flow.description && (
                      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                        {flow.description}
                      </p>
                    )}
                    <div className="mt-4 text-right">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300">
                        {flow.model.split('/')[0]}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : showThreads ? (
        // Thread selection screen
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center justify-between mb-8">
            <div>
              <button
                onClick={() => {
                  setSelectedFlow(null);
                  setShowThreads(false);
                  router.push('/chat');
                }}
                className="group flex items-center text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 mb-2 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1 group-hover:translate-x-[-2px] transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to flows
              </button>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-500 to-purple-600 text-transparent bg-clip-text">
                Chats with {selectedFlow.name}
              </h1>
            </div>
            
            <button
              onClick={handleNewThread}
              className="px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all flex items-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Chat
            </button>
          </div>

          {threads.length === 0 ? (
            <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm shadow-lg rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
              <div className="mb-6">
                <div className="inline-block p-3 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-6 text-lg">No conversations yet.</p>
              <button
                onClick={handleNewThread}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all"
              >
                Start a new chat
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {threads.map(thread => (
                <div 
                  key={thread.id} 
                  className="group bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm shadow-md hover:shadow-lg rounded-lg p-4 cursor-pointer hover:bg-white dark:hover:bg-gray-750 transition-all relative overflow-hidden border border-gray-200 dark:border-gray-700"
                  onClick={() => handleThreadSelect(thread.id)}
                >
                  <div className="absolute top-0 left-0 h-full w-1 bg-gradient-to-b from-indigo-500 to-purple-600"></div>
                  <div className="flex justify-between items-start pl-3">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        {thread.title}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {thread.message_count} {thread.message_count === 1 ? 'message' : 'messages'} · 
                        {' '}{new Date(thread.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteThread(thread.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 dark:text-gray-500 dark:hover:text-red-400 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-all"
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
        <div className="flex flex-col h-[calc(100vh-12rem)] animate-fade-in">
          <div className="flex justify-between items-center mb-6">
            <div>
              <button
                onClick={() => {
                  setShowThreads(true);
                  router.push(`/chat?flow=${selectedFlow.id}`);
                }}
                className="group flex items-center text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 mb-2 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1 group-hover:translate-x-[-2px] transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to chats
              </button>
              
              <div className="flex items-center">
                {editingTitle ? (
                  <div className="flex mt-2">
                    <input
                      ref={titleInputRef}
                      type="text"
                      value={threadTitle}
                      onChange={(e) => setThreadTitle(e.target.value)}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleTitleUpdate();
                        }
                      }}
                    />
                    <button
                      onClick={handleTitleUpdate}
                      className="ml-2 px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingTitle(false)}
                      className="ml-2 px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <h1 className="text-2xl font-bold flex items-center">
                    {threadTitle || "New Chat"}
                    {selectedThread && (
                      <button
                        onClick={() => setEditingTitle(true)}
                        className="ml-2 text-gray-400 hover:text-indigo-600 dark:text-gray-500 dark:hover:text-indigo-400 transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                    )}
                  </h1>
                )}
              </div>
              
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                <span className="inline-block h-2 w-2 rounded-full bg-green-400 mr-1"></span>
                Flow: {selectedFlow.name}
              </p>
            </div>
            
            <button
              onClick={handleNewThread}
              className="px-3 py-1.5 border border-transparent rounded-lg shadow-sm text-xs font-medium text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transition-all flex items-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Chat
            </button>
          </div>
          
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border-l-4 border-red-500 p-4 mb-4 rounded-r-lg">
              <div className="flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-red-700 dark:text-red-400">{error}</p>
              </div>
            </div>
          )}
          
          <div className="flex-grow bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm shadow-lg rounded-xl mb-4 overflow-y-auto border border-gray-200 dark:border-gray-700">
            <div className="p-6 space-y-6">
              {messages.length === 0 ? (
                <div className="text-center py-16">
                  <div className="inline-block p-3 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <p className="text-gray-500 dark:text-gray-400 text-lg">
                    Start a conversation with this flow.
                  </p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div 
                    key={index}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                  >
                    <div 
                      className={`max-w-[80%] px-5 py-3 rounded-2xl ${
                        msg.role === 'user' 
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md' 
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm border border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <div className={`text-xs mt-1 ${msg.role === 'user' ? 'text-indigo-200' : 'text-gray-400'}`}>
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="relative flex-grow">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={loading}
                placeholder="Type your message..."
                className="w-full px-4 py-3 pr-10 border border-gray-300 dark:border-gray-600 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white placeholder-gray-400"
              />
              {message && (
                <button 
                  type="button" 
                  onClick={() => setMessage("")}
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={loading || !message.trim()}
              className="px-4 py-3 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all min-w-[4.5rem] flex items-center justify-center"
            >
              {loading ? (
                <div className="h-5 w-5 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
              ) : (
                <span className="flex items-center">
                  Send
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </span>
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  );
} 