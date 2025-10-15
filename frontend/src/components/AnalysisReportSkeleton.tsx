import React from 'react';
import Card from './Card';

const Skeleton = ({ className = '' }: { className?: string }) => (
  <div className={`bg-base-300 animate-pulse rounded-md ${className}`} />
);

const AnalysisReportSkeleton = () => (
  <div className="space-y-6 animate-fade-in">
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <Card className="p-6">
          <Skeleton className="h-6 w-1/3 mb-4" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </Card>
      </div>
      <div className="space-y-6">
        <Card className="p-6">
          <Skeleton className="h-5 w-1/4 mb-4" />
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </Card>
        <Card className="p-6">
          <Skeleton className="h-5 w-1/3 mb-4" />
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </Card>
      </div>
    </div>
    <Card className="p-6">
      <Skeleton className="h-6 w-1/4 mb-6" />
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    </Card>
  </div>
);

export default AnalysisReportSkeleton;