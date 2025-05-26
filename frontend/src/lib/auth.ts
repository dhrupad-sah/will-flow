"use client";

import { useState, useEffect } from 'react';

/**
 * Simple client-side auth utility for handling email-based authentication
 */

export const getUserEmail = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('userEmail');
};

export const setUserEmail = (email: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('userEmail', email);
};

export const clearUserEmail = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('userEmail');
};

export const isAuthenticated = (): boolean => {
  return !!getUserEmail();
};

export const useAuth = () => {
  const [userEmail, setUserEmailState] = useState<string | null>(null);
  
  useEffect(() => {
    setUserEmailState(getUserEmail());
  }, []);
  
  const login = (email: string) => {
    setUserEmail(email);
    setUserEmailState(email);
  };
  
  const logout = () => {
    clearUserEmail();
    setUserEmailState(null);
  };
  
  return {
    userEmail,
    isAuthenticated: !!userEmail,
    login,
    logout
  };
}; 