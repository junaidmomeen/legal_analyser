import React, { useState } from 'react';
import { Search, Download, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';
import Card from './Card';
import Button from './Button';
import EnhancedSummary from './EnhancedSummary';

interface KeyClause {
  type: string;
  content: string;
  importance: 'high' | 'medium' | 'low';
  classification: string;
  risk_score: number;
  page?: number;
}

interface AnalysisResult {
  summary: string;
  key_clauses: KeyClause[];
  document_type: string;
  total_pages: number;
  word_count: number;
  analyzed_at: string;
  file_id?: string;
}

interface DashboardProps {
  analysis: AnalysisResult;
  onExport: (format: 'pdf' | 'json') => void;
  onViewOriginal: () => void;
  onReset: () => void;
  onClearHistory: () => void;
  selectedFile: File | null;
}

const getImportanceClass = (importance: string) => {
  switch (importance) {
    case 'high':
      return 'bg-error/10 border-error/20 text-error';
    case 'medium':
      return 'bg-warning/10 border-warning/20 text-warning';
    case 'low':
      return 'bg-success/10 border-success/20 text-success';
    default:
      return 'bg-base-300 border-base-300 text-neutral';
  }
};

const ClauseCard = ({ clause }: { clause: KeyClause }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card className={`mb-4 p-4 transition-all duration-300 ${getImportanceClass(clause.importance)}`}>
      <div className="flex justify-between items-center cursor-pointer" onClick={() => setIsOpen(!isOpen)}>
        <h4 className="font-semibold text-md text-gray-200">{clause.type}</h4>
        <div className="flex items-center space-x-4">
          <span className={`text-sm font-medium px-2 py-1 rounded-full ${getImportanceClass(clause.importance)}`}>
            {clause.importance}
          </span>
          {isOpen ? <ChevronUp /> : <ChevronDown />}
        </div>
      </div>
      {isOpen && (
        <div className="mt-4 animate-fade-in">
          <p className="text-neutral">{clause.content}</p>
          <div className="mt-4 flex justify-between text-sm text-neutral/80">
            <span>Risk Score: {clause.risk_score}/10</span>
            <span>Page: {clause.page || 'N/A'}</span>
          </div>
        </div>
      )}
    </Card>
  );
};

const Dashboard: React.FC<DashboardProps> = ({ analysis, onExport, onViewOriginal, onReset, onClearHistory, selectedFile }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [importanceFilter, setImportanceFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const filteredClauses = analysis.key_clauses.filter((clause: KeyClause) => {
    const searchTermLower = searchTerm.toLowerCase();
    const matchesSearchTerm = clause.content.toLowerCase().includes(searchTermLower) || clause.type.toLowerCase().includes(searchTermLower);
    const matchesImportance = importanceFilter === 'all' || clause.importance === importanceFilter;
    return matchesSearchTerm && matchesImportance;
  });

  return (
    <div className="animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="p-6">
            <h3 className="text-xl font-bold mb-6 text-gray-200">Analysis Summary</h3>
            <EnhancedSummary summary={analysis.summary} />
          </Card>
        </div>
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4 text-gray-200">Document Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-neutral">File Name:</span>
                <span className="font-semibold text-gray-200">{selectedFile?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral">Document Type:</span>
                <span className="font-semibold text-gray-200">{analysis.document_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral">Total Pages:</span>
                <span className="font-semibold text-gray-200">{analysis.total_pages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral">Word Count:</span>
                <span className="font-semibold text-gray-200">{analysis.word_count}</span>
              </div>
            </div>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4 text-gray-200">Actions</h3>
            <div className="flex flex-col space-y-3">
              <Button onClick={() => onExport('pdf')} variant="primary"><Download className="h-4 w-4" /><span>Export File (PDF)</span></Button>
              <Button onClick={() => onExport('json')} variant="secondary"><Download className="h-4 w-4" /><span>Export File (JSON)</span></Button>
              <Button onClick={onViewOriginal} variant="tertiary"><span>View Original Document</span></Button>
              <Button onClick={onReset} variant="primary"><span>New Analysis</span></Button>
              <Button onClick={onClearHistory} variant="danger"><Trash2 className="h-4 w-4" /><span>Clear History</span></Button>
            </div>
          </Card>
        </div>
      </div>

      <div className="mt-8">
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4 text-gray-200">Key Clauses</h3>
          <div className="flex flex-col md:flex-row justify-between items-center mb-4 gap-4">
            <div className="relative w-full md:w-1/2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral/50" />
              <input
                type="text"
                placeholder="Search clauses..."
                className="w-full bg-base-200 border border-base-300 rounded-md pl-10 pr-4 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="w-full md:w-auto">
              <select
                className="w-full bg-base-200 border border-base-300 rounded-md px-4 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={importanceFilter}
                onChange={(e) => setImportanceFilter(e.target.value as 'all' | 'high' | 'medium' | 'low')}
              >
                <option value="all">All Importance</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
          <div>
            {filteredClauses.map((clause, index) => (
              <ClauseCard key={index} clause={clause} />
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
