import React from 'react';

const StudioPage: React.FC = () => {
  return (
    <section className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-5xl font-light mb-8">Studio</h2>
        <p className="text-lg leading-relaxed text-gray-300 mb-8">
          AETHER is a design house rooted in the philosophy of radical minimalism and tactile luxury. 
          Each piece is conceived in our Berlin atelier, where traditional craftsmanship meets digital precision.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-12">
          <div className="p-6 bg-gray-900">
            <h3 className="text-xl font-light mb-2">Design</h3>
            <p className="text-gray-400">Concept-driven collections exploring form, texture, and restraint.</p>
          </div>
          <div className="p-6 bg-gray-900">
            <h3 className="text-xl font-light mb-2">Craft</h3>
            <p className="text-gray-400">Hand-finished details, organic textiles, and archival techniques.</p>
          </div>
          <div className="p-6 bg-gray-900">
            <h3 className="text-xl font-light mb-2">Ethos</h3>
            <p className="text-gray-400">Sustainable production, genderless silhouettes, timeless wear.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default StudioPage;