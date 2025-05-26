'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PlusIcon, TrashIcon, DocumentIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/lib/auth';
import { KnowledgeBase, listKnowledgeBases, createKnowledgeBase, deleteKnowledgeBase } from '@/lib/api';

export default function KnowledgeBasePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDescription, setNewKBDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const { userEmail } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!userEmail) return;

    const fetchKnowledgeBases = async () => {
      try {
        const kbs = await listKnowledgeBases(userEmail);
        setKnowledgeBases(kbs);
      } catch (error) {
        console.error('Failed to fetch knowledge bases:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchKnowledgeBases();
  }, [userEmail]);

  const handleCreateKB = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userEmail || !newKBName.trim()) return;

    setIsCreating(true);
    try {
      const newKB = await createKnowledgeBase(
        { name: newKBName, description: newKBDescription || undefined },
        userEmail
      );
      setKnowledgeBases([newKB, ...knowledgeBases]);
      setNewKBName('');
      setNewKBDescription('');
    } catch (error) {
      console.error('Failed to create knowledge base:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteKB = async (kbId: string) => {
    if (!confirm('Are you sure you want to delete this knowledge base? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteKnowledgeBase(kbId);
      setKnowledgeBases(knowledgeBases.filter(kb => kb.id !== kbId));
    } catch (error) {
      console.error('Failed to delete knowledge base:', error);
    }
  };

  const navigateToKB = (kbId: string) => {
    router.push(`/knowledge-base/${kbId}`);
  };

  if (!userEmail) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-24">
        <p className="text-xl">Please sign in to view your knowledge bases.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Your Knowledge Bases</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Create New Knowledge Base</h2>
        <form onSubmit={handleCreateKB} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={newKBName}
              onChange={(e) => setNewKBName(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
              placeholder="My Knowledge Base"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description (optional)</label>
            <textarea
              value={newKBDescription}
              onChange={(e) => setNewKBDescription(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
              placeholder="A brief description of your knowledge base"
              rows={2}
            />
          </div>
          <button
            type="submit"
            disabled={isCreating || !newKBName.trim()}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            {isCreating ? 'Creating...' : 'Create Knowledge Base'}
          </button>
        </form>
      </div>

      {isLoading ? (
        <div className="text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          <p className="mt-2">Loading knowledge bases...</p>
        </div>
      ) : knowledgeBases.length === 0 ? (
        <div className="text-center py-10 bg-white dark:bg-gray-800 rounded-lg shadow">
          <p className="text-xl">You don't have any knowledge bases yet.</p>
          <p className="mt-2">Create one to get started!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {knowledgeBases.map((kb) => (
            <div
              key={kb.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden hover:shadow-md transition-shadow"
            >
              <div 
                className="p-6 cursor-pointer"
                onClick={() => navigateToKB(kb.id)}
              >
                <div className="flex justify-between items-start">
                  <h3 className="text-xl font-semibold mb-2">{kb.name}</h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteKB(kb.id);
                    }}
                    className="text-red-500 hover:text-red-700"
                    title="Delete knowledge base"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
                {kb.description && <p className="text-gray-600 dark:text-gray-300 mb-4">{kb.description}</p>}
                <div className="flex items-center text-sm text-gray-500">
                  <DocumentIcon className="w-4 h-4 mr-1" />
                  <span>{kb.documents.length} document(s)</span>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Created: {new Date(kb.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 