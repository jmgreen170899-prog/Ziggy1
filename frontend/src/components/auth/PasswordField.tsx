import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { EyeIcon, EyeOffIcon } from 'lucide-react';

interface PasswordFieldProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  id?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  showStrengthMeter?: boolean;
  'aria-describedby'?: string;
}

const getPasswordStrength = (password: string): { score: number; text: string; color: string } => {
  let score = 0;
  
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  
  if (score <= 2) return { score, text: 'Weak', color: 'bg-danger' };
  if (score <= 4) return { score, text: 'Fair', color: 'bg-warning' };
  if (score <= 5) return { score, text: 'Good', color: 'bg-blue-500' };
  return { score, text: 'Strong', color: 'bg-success' };
};

export const PasswordField: React.FC<PasswordFieldProps> = ({
  value,
  onChange,
  placeholder = 'Enter your password',
  label,
  id,
  required = false,
  disabled = false,
  error,
  showStrengthMeter = false,
  'aria-describedby': ariaDescribedBy,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  
  const strength = showStrengthMeter ? getPasswordStrength(value) : null;
  const strengthId = id ? `${id}-strength` : undefined;
  const errorId = id ? `${id}-error` : undefined;
  
  const describedBy = [
    ariaDescribedBy,
    error ? errorId : undefined,
    showStrengthMeter ? strengthId : undefined,
  ].filter(Boolean).join(' ') || undefined;

  return (
    <div className="space-y-2">
      {label && (
        <label 
          htmlFor={id}
          className="text-sm font-medium text-fg"
        >
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <input
          type={showPassword ? 'text' : 'password'}
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          aria-describedby={describedBy}
          aria-invalid={error ? 'true' : 'false'}
          className={`
            w-full px-3 py-2 pr-10 text-sm
            bg-surface border rounded-md
            placeholder:text-fg-muted
            focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error 
              ? 'border-danger focus:ring-danger' 
              : 'border-border hover:border-border-hover'
            }
          `}
        />
        
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowPassword(!showPassword)}
          disabled={disabled}
          className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover:bg-surface-hover"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? (
            <EyeOffIcon className="h-4 w-4" />
          ) : (
            <EyeIcon className="h-4 w-4" />
          )}
        </Button>
      </div>
      
      {error && (
        <p 
          id={errorId}
          className="text-sm text-danger"
          role="alert"
        >
          {error}
        </p>
      )}
      
      {showStrengthMeter && value && (
        <div id={strengthId} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-fg-muted">Password strength:</span>
            <span className={`font-medium ${
              strength?.text === 'Strong' ? 'text-success' :
              strength?.text === 'Good' ? 'text-blue-500' :
              strength?.text === 'Fair' ? 'text-warning' :
              'text-danger'
            }`}>
              {strength?.text}
            </span>
          </div>
          <div className="w-full bg-surface rounded-full h-1.5">
            <div 
              className={`h-1.5 rounded-full transition-all duration-300 ${strength?.color}`}
              style={{ width: `${((strength?.score || 0) / 6) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};