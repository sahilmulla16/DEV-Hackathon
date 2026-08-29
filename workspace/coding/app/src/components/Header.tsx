import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <header className="border-b border-gray-800 px-6 py-4 flex justify-between items-center">
      <h1 className="text-2xl font-bold tracking-tight">AETHER</h1>
      <nav>
        <ul className="flex space-x-8 text-sm uppercase tracking-wider">
          <li><Link to="/" className="hover:text-gray-400 transition">Collections</Link></li>
          <li><Link to="/editorial" className="hover:text-gray-400 transition">Editorial</Link></li>
          <li><Link to="/studio" className="hover:text-gray-400 transition">Studio</Link></li>
          <li><Link to="/journal" className="hover:text-gray-400 transition">Journal</Link></li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;