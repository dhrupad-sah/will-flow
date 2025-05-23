"use client";

import { useState } from "react";
import { FlowCreate, FlowUpdate, AVAILABLE_MODELS } from "@/lib/api";

interface FlowFormProps {
  initialData?: FlowUpdate;
  onSubmit: (data: any) => Promise<void>;
  isEdit?: boolean;
}

export default function FlowForm({ initialData, onSubmit, isEdit = false }: FlowFormProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [systemPrompt, setSystemPrompt] = useState(initialData?.system_prompt || "");
  const [model, setModel] = useState(initialData?.model || AVAILABLE_MODELS[0].id);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = isEdit
        ? { name, description, system_prompt: systemPrompt, model }
        : { name, description, system_prompt: systemPrompt, model, creator_email: "" }; // Creator email will be set by the parent component
        
      await onSubmit(data);
    } catch (err) {
      console.error(err);
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Flow Name
        </label>
        <div className="mt-1">
          <input
            id="name"
            name="name"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            placeholder="Give your flow a name"
          />
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Description (optional)
        </label>
        <div className="mt-1">
          <input
            id="description"
            name="description"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            placeholder="Briefly describe what this flow does"
          />
        </div>
      </div>

      <div>
        <label htmlFor="systemPrompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          System Prompt
        </label>
        <div className="mt-1">
          <textarea
            id="systemPrompt"
            name="systemPrompt"
            rows={5}
            required
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            className="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            placeholder="You are a helpful assistant that..."
          />
        </div>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          This defines the behavior and capabilities of your AI flow.
        </p>
      </div>

      <div>
        <label htmlFor="model" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          AI Model
        </label>
        <div className="mt-1">
          <select
            id="model"
            name="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="appearance-none block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
          >
            {AVAILABLE_MODELS.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="text-red-500 text-sm">
          {error}
        </div>
      )}

      <div>
        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? 'Saving...' : isEdit ? 'Update Flow' : 'Create Flow'}
        </button>
      </div>
    </form>
  );
} 