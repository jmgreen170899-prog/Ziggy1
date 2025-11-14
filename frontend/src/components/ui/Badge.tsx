import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'destructive' | 'secondary' | 'outline';
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'default', 
  className = '' 
}) => {
  const baseClasses = 'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border transition-all duration-200 hover:shadow-md';
  
  const variantClasses = {
    default: 'bg-primary-tech-blue/10 text-primary-tech-blue border-primary-tech-blue/30 dark:bg-secondary-cyan/20 dark:text-secondary-cyan dark:border-secondary-cyan/50',
    destructive: 'bg-danger/10 text-danger border-danger/30 dark:bg-danger/20 dark:text-danger dark:border-danger/50',
    secondary: 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
    outline: 'bg-transparent border-2 border-border text-fg dark:border-border dark:text-fg'
  };

  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};

export { Badge };