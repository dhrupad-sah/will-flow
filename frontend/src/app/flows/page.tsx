"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Flow, listFlows } from "@/lib/api";
import { getUserEmail, isAuthenticated } from "@/lib/auth";

export default function FlowsPage() {
  const [flows, setFlows] = useState<Flow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      router.push('/');
      return;
    }

    const fetchFlows = async () => {
      try {
        const userEmail = getUserEmail();
        const flowsData = await listFlows(userEmail || undefined);
        setFlows(flowsData);
      } catch (err) {
        console.error(err);
        setError('Failed to load flows');
      } finally {
        setLoading(false);
      }
    };

    fetchFlows();
  }, [router]);

  const handleDeleteFlow = async (flowId: string) => {
    // Add confirmation dialog
    if (!confirm("Are you sure you want to delete this flow?")) {
      return;
    }

    try {
      setLoading(true);
      // Call delete API
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/flows/${flowId}`, {
        method: 'DELETE',
      });
      
      // Refresh flows
      const userEmail = getUserEmail();
      const flowsData = await listFlows(userEmail || undefined);
      setFlows(flowsData);
    } catch (err) {
      console.error(err);
      setError('Failed to delete flow');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Loading flows...
        </h1>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Your Flows
        </h1>
        <Link 
          href="/flows/new"
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Create New Flow
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border-l-4 border-red-500 p-4 mb-6">
          <p className="text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {flows.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg p-6 text-center">
          <p className="text-gray-600 dark:text-gray-400">You haven't created any flows yet.</p>
          <Link 
            href="/flows/new"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Create your first flow
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {flows.map((flow) => (
            <div 
              key={flow.id} 
              className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg"
            >
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                  {flow.name}
                </h3>
                {flow.description && (
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    {flow.description}
                  </p>
                )}
              </div>
              <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-4 sm:px-6 flex justify-between">
                <Link 
                  href={`/chat?flow=${flow.id}`}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                >
                  Chat
                </Link>
                <div className="flex space-x-2">
                  <Link 
                    href={`/flows/${flow.id}`}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
                  >
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDeleteFlow(flow.id)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 