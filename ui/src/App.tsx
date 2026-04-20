import React, { useEffect } from 'react';
import Dashboard from './components/Dashboard';
import toast, { Toaster } from 'react-hot-toast';
import apiClient from './services/api';

const App: React.FC = () => {
  useEffect(() => {
    // Check API health on startup
    const checkHealth = async () => {
      try {
        const health = await apiClient.getHealth();
        console.log('✓ API Health:', health);
      } catch (error) {
        console.error('✗ API connection failed');
        toast.error('Failed to connect to API');
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="bg-slate-900">
      <Dashboard />
      <Toaster position="bottom-right" />
    </div>
  );
};

export default App;