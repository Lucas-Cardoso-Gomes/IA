import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AdminDashboard from './pages/AdminDashboard';
import NotebookWorkspace from './pages/NotebookWorkspace';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/notebook/:id" element={<NotebookWorkspace />} />
          <Route path="/" element={<NotebookWorkspace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
