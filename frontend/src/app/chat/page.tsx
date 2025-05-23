"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Flow, Message, getFlowById, listFlows, sendChatMessage } from "@/lib/api";
import { getUserEmail, isAuthenticated } from "@/lib/auth";

export default function ChatPage() {
  const [selectedFlow, setSelectedFlow] = useState<Flow | null>(null);
  const [availableFlows, setAvailableFlows] = useState<Flow[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingFlows, setLoadingFlows] = useState(true);
  const [error, setError] = useState("");
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const flowIdFromUrl = searchParams.get('flow');

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
        }
      } catch (err) {
        console.error(err);
        setError('Failed to load flows');
      } finally {
        setLoadingFlows(false);
      }
    };
    
    fetchFlows();
  }, [flowIdFromUrl, router]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle flow selection
  const handleFlowSelect = async (flowId: string) => {
    try {
      const flow = await getFlowById(flowId);
      setSelectedFlow(flow);
      setMessages([]);
      setSessionId(null);
      
      // Update URL
      router.push(`/chat?flow=${flowId}`);
    } catch (err) {
      console.error(err);
      setError('Failed to select flow');
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
        session_id: sessionId || undefined
      });
      
      // Update messages and session ID
      setMessages(response.messages);
      setSessionId(response.session_id);
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
      ) : (
        <div className="flex flex-col h-[calc(100vh-10rem)]">
          <div className="flex justify-between items-center mb-4">
            <div>
              <button
                onClick={() => {
                  setSelectedFlow(null);
                  router.push('/chat');
                }}
                className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                &larr; Back to flows
              </button>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                {selectedFlow.name}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {selectedFlow.description || 'No description provided'}
              </p>
            </div>
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