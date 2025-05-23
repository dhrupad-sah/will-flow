"use client";

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