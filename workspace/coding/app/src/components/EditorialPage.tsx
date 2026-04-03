import React from 'react';

const EditorialPage: React.FC = () => {
  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-5xl font-light mb-12 border-b border-gray-800 pb-6">Editorial</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <article className="group cursor-pointer">
            <img
              src="https://source.unsplash.com/random/800x600/?model,monochrome"
              alt="Editorial 1"
              className="w-full h-96 object-cover mb-4 group-hover:scale-105 transition transform"
            />
            <h3 className="text-2xl font-light">Silhouettes in Concrete</h3>
            <p className="text-gray-400 mt-2">Photography by Lena Voss</p>
          </article>
          <article className="group cursor-pointer">
            <img
              src="https://source.unsplash.com/random/800x600/?fashion,architecture"
              alt="Editorial 2"
              className="w-full h-96 object-cover mb-4 group-hover:scale-105 transition transform"
            />
            <h3 className="text-2xl font-light">Brutalism Reimagined</h3>
            <p className="text-gray-400 mt-2">Styled by Malik Chen</p>
          </article>
        </div>
      </div>
    </section>
  );
};

export default EditorialPage;