import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './components/HomePage';
import EditorialPage from './components/EditorialPage';
import StudioPage from './components/StudioPage';
import JournalPage from './components/JournalPage';

const Router: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout /> }>
        <Route index element={<HomePage />} />
        <Route path="editorial" element={<EditorialPage />} />
        <Route path="studio" element={<StudioPage />} />
        <Route path="journal" element={<JournalPage />} />
      </Route>
    </Routes>
  );
};

export default Router;