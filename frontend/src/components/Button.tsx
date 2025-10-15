import React from 'react';

const Button = ({ children, onClick, disabled = false, variant = 'primary', className = '' }: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'tertiary' | 'danger';
  className?: string;
}) => {
  const baseClasses = 'px-4 py-2 font-semibold rounded-md transition-all duration-300 flex items-center justify-center space-x-2 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-100';
  const variantClasses = {
    primary: 'bg-primary hover:bg-secondary text-white shadow-sm hover:shadow-md disabled:bg-primary/50 disabled:cursor-not-allowed focus:ring-primary',
    secondary: 'bg-base-300 hover:bg-neutral/20 text-gray-200 disabled:bg-base-200/50 disabled:cursor-not-allowed focus:ring-neutral',
    tertiary: 'bg-transparent hover:bg-neutral/10 text-gray-200 disabled:bg-transparent disabled:cursor-not-allowed focus:ring-neutral',
    danger: 'bg-error hover:bg-error/80 text-white shadow-sm hover:shadow-md disabled:bg-error/50 disabled:cursor-not-allowed focus:ring-error',
  };
  return (
    <button onClick={onClick} disabled={disabled} className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </button>
  );
};

export default Button;