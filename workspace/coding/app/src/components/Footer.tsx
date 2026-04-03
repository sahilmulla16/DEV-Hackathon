import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="border-t border-gray-800 px-6 py-8 text-sm text-gray-500">
      <div className="flex justify-between">
        <p>&copy; {new Date().getFullYear()} AETHER. All rights reserved.</p>
        <div className="flex space-x-6">
          <a href="#" className="hover:text-white transition">Instagram</a>
          <a href="#" className="hover:text-white transition">Privacy</a>
          <a href="#" className="hover:text-white transition">Contact</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;