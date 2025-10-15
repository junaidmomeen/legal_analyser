import React from 'react';
import Card from './Card';
import Button from './Button';

const ConfirmationDialog = ({ message, onConfirm, onCancel }: { message: string, onConfirm: () => void, onCancel: () => void }) => (
  <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
    <Card className="p-8 max-w-sm w-full animate-slide-in-from-bottom">
      <div className="text-center">
        <h3 className="text-lg font-bold text-gray-800 mb-2">Are you sure?</h3>
        <p className="text-neutral mb-6">{message}</p>
        <div className="flex justify-center space-x-4">
          <Button onClick={onCancel} variant="secondary">Cancel</Button>
          <Button onClick={onConfirm} variant="primary">Confirm</Button>
        </div>
      </div>
    </Card>
  </div>
);

export default ConfirmationDialog;