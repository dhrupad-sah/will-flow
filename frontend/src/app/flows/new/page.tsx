"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import Link from "next/link";
import { FlowCreate, createFlow } from "@/lib/api";
import { getUserEmail, isAuthenticated } from "@/lib/auth";
import FlowForm from "@/components/FlowForm";

export default function NewFlowPage() {
  const [error, setError] = useState("");
  const router = useRouter();
  
  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      router.push('/');
    }
  }, [router]);

  const handleSubmit = async (data: FlowCreate) => {
    try {
      // Add creator email
      const userEmail = getUserEmail();
      if (!userEmail) {
        throw new Error("User not authenticated");
      }
      
      data.creator_email = userEmail;
      
      // Create flow
      await createFlow(data);
      
      // Redirect to flows page
      router.push('/flows');
    } catch (err) {
      console.error(err);
      setError('Failed to create flow. Please try again.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <Link
          href="/flows"
          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        >
          &larr; Back to flows
        </Link>
      </div>
      
      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg p-6">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
          Create New Flow
        </h1>
        
        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border-l-4 border-red-500 p-4 mb-6">
            <p className="text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}
        
        <FlowForm onSubmit={handleSubmit} />
      </div>
    </div>
  );
} 