import React from 'react';

const JournalPage: React.FC = () => {
  return (
    <section className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-5xl font-light mb-12">Journal</h2>
        <article className="mb-12">
          <h3 className="text-2xl font-light mb-2">The Silence Between Stitches</h3>
          <p className="text-sm text-gray-500 mb-4">October 12, 2024 — Essay by Clara Meier</p>
          <p className="text-gray-300 leading-relaxed">
            In a world of noise, the most radical act is restraint. The pause between gestures, 
            the space between fabric and skin — that is where meaning emerges.
          </p>
        </article>
        <article>
          <h3 className="text-2xl font-light mb-2">Material Futures</h3>
          <p className="text-sm text-gray-500 mb-4">September 28, 2024 — Interview</p>
          <p className="text-gray-300 leading-relaxed">
            We speak with textile innovator Jun Liu about bio-silk, zero-waste weaving, 
            and the emotional intelligence of fabric.
          </p>
        </article>
      </div>
    </section>
  );
};

export default JournalPage;