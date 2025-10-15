import React from 'react';

const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`bg-base-200 border border-base-300 rounded-lg shadow-sm ${className}`}>
    {children}
  </div>
);

export default Card;