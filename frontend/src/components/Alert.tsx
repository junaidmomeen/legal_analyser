import { AlertCircle, X } from 'lucide-react';
import { ApiError } from '../api/api';

const Alert = ({ error, onClose }: { error: ApiError; onClose: () => void }) => (
  <div className="mt-4 p-4 bg-error/10 border border-error/20 rounded-lg flex items-center justify-between space-x-3">
    <div className="flex items-center space-x-2">
      <AlertCircle className="h-5 w-5 text-error flex-shrink-0" />
      <p className="text-error">{error.message}</p>
    </div>
    <button onClick={onClose} className="text-error/70 hover:text-error">
      <X className="h-5 w-5" />
    </button>
  </div>
);

export default Alert;