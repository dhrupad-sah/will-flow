import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  color = 'indigo', 
  text 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div 
        className={`${sizeClasses[size]} rounded-full border-t-transparent border-${color}-600 animate-spin`}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <p className={`mt-2 text-${color}-600 dark:text-${color}-400 text-sm font-medium`}>
          {text}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner; 