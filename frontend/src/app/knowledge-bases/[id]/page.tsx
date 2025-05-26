'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { ArrowUpTrayIcon, PaperClipIcon, PaperAirplaneIcon, CheckIcon, XMarkIcon, ClockIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/lib/auth';
import { 
  getKnowledgeBase, 
  KnowledgeBase, 
  DocumentInfo, 
  uploadDocument, 
  getDocumentStatus, 
  chatWithKnowledgeBase,
  ChatWithKbResponse
} from '@/lib/api';

export default function KnowledgeBaseDetailPage() {
  const params = useParams();
  const { id } = params;
  const { userEmail } = useAuth();
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, DocumentInfo>>({});
  const [query, setQuery] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<Array<{
    role: 'user' | 'assistant';
    content: string;
    citations?: Array<{
      doc_id: string;
      text: string;
      score: number;
      file_name: string;
    }>;
  }>>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id || !userEmail) return;

    const fetchKnowledgeBase = async () => {
      try {
        const kbData = await getKnowledgeBase(id as string);
        setKb(kbData);
        
        // Start polling for document statuses
        const processingDocs = kbData.documents.filter(doc => doc.status === 'processing');
        processingDocs.forEach(doc => {
          pollDocumentStatus(kbData.id, doc.doc_id);
        });
      } catch (error) {
        console.error('Failed to fetch knowledge base:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchKnowledgeBase();
  }, [id, userEmail]);

  useEffect(() => {
    // Scroll to bottom of messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const pollDocumentStatus = async (kbId: string, docId: string, attempts = 0) => {
    if (attempts > 20) return; // Limit polling attempts

    try {
      const docInfo = await getDocumentStatus(kbId, docId);
      
      // Update document status in state
      setKb(prevKb => {
        if (!prevKb) return null;
        
        const updatedDocs = prevKb.documents.map(doc => 
          doc.doc_id === docId ? docInfo : doc
        );
        
        return {
          ...prevKb,
          documents: updatedDocs
        };
      });
      
      // Continue polling if still processing
      if (docInfo.status === 'processing') {
        setTimeout(() => pollDocumentStatus(kbId, docId, attempts + 1), 3000);
      }
    } catch (error) {
      console.error('Error polling document status:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !kb || !kb.id) return;
    
    setIsUploading(true);
    try {
      const docInfo = await uploadDocument(kb.id, selectedFile);
      
      // Update KB with new document
      setKb(prevKb => {
        if (!prevKb) return null;
        return {
          ...prevKb,
          documents: [...prevKb.documents, docInfo]
        };
      });
      
      // Start polling for document status
      pollDocumentStatus(kb.id, docInfo.doc_id);
      
      // Reset file input
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Failed to upload document:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !kb || !kb.id || !userEmail || isSending) return;
    
    const userQuery = query.trim();
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setQuery('');
    setIsSending(true);
    
    try {
      const response = await chatWithKnowledgeBase(kb.id, userQuery, userEmail);
      
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: response.answer,
          citations: response.citations
        }
      ]);
    } catch (error) {
      console.error('Failed to get response:', error);
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: 'Sorry, I encountered an error while processing your request.'
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  if (!userEmail) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-24">
        <p className="text-xl">Please sign in to view this knowledge base.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        <p className="mt-4">Loading knowledge base...</p>
      </div>
    );
  }

  if (!kb) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-24">
        <p className="text-xl">Knowledge base not found.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 flex flex-col min-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{kb.name}</h1>
        {kb.description && <p className="text-gray-600 dark:text-gray-300 mt-2">{kb.description}</p>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-grow">
        {/* Left sidebar - Documents */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 lg:col-span-1">
          <h2 className="text-xl font-semibold mb-4">Documents</h2>
          
          <div className="mb-6">
            <div className="flex items-center space-x-3 mb-4">
              <label 
                htmlFor="fileUpload"
                className="flex-1 px-4 py-2 border border-dashed border-gray-300 dark:border-gray-600 rounded-md text-center cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <div className="flex items-center justify-center">
                  <ArrowUpTrayIcon className="w-5 h-5 mr-2" />
                  <span>{selectedFile ? selectedFile.name : "Select File"}</span>
                </div>
                <input
                  id="fileUpload"
                  type="file"
                  className="hidden"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </label>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
          
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {kb.documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No documents yet</p>
                <p className="text-sm mt-1">Upload documents to start asking questions</p>
              </div>
            ) : (
              kb.documents.map((doc) => (
                <div 
                  key={doc.doc_id} 
                  className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md flex items-start"
                >
                  <PaperClipIcon className="w-5 h-5 mr-3 text-gray-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{doc.file_name}</div>
                    <div className="flex items-center mt-1 text-sm">
                      <span 
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                          doc.status === 'ready' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                            : doc.status === 'processing'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}
                      >
                        {doc.status === 'ready' ? (
                          <><CheckIcon className="w-3 h-3 mr-1" /> Ready</>
                        ) : doc.status === 'processing' ? (
                          <><ClockIcon className="w-3 h-3 mr-1" /> Processing</>
                        ) : (
                          <><XMarkIcon className="w-3 h-3 mr-1" /> Failed</>
                        )}
                      </span>
                      <span className="mx-2">•</span>
                      <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right section - Chat */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 flex flex-col lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Chat with your Knowledge Base</h2>
          
          <div className="flex-grow overflow-y-auto mb-4 space-y-4 max-h-[500px]">
            {messages.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                <p>Ask a question about your documents</p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div 
                    className={`rounded-lg px-4 py-2 max-w-[80%] ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600 text-xs">
                        <div className="font-semibold mb-1">Sources:</div>
                        <ul className="space-y-1">
                          {msg.citations.map((citation, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="inline-block w-4 text-right mr-1">{idx + 1}.</span>
                              <span className="truncate">{citation.file_name}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <form onSubmit={handleSendQuery} className="mt-auto">
            <div className="flex items-center">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about your documents..."
                className="flex-1 px-4 py-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
                disabled={isSending}
              />
              <button
                type="submit"
                disabled={!query.trim() || isSending}
                className="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isSending ? (
                  <div className="w-5 h-5 border-t-2 border-white rounded-full animate-spin"></div>
                ) : (
                  <PaperAirplaneIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
} 