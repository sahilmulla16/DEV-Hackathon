import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-off-white text-soft-black">
      <Header />
      <Hero />
      <EditorialSection />
      <InteractiveLookbook />
      <Footer />
    </div>
  );
}

const Header = () => (
  <header className="flex justify-between items-center p-6 md:p-10 border-b border-warm-gray">
    <h1 className="text-2xl md:text-4xl font-bold tracking-tight">MAISON NOIR</h1>
    <nav>
      <ul className="flex space-x-8 text-sm uppercase tracking-wider">
        <li><a href="#editorial" className="hover:underline">Editorial</a></li>
        <li><a href="#collection" className="hover:underline">Collection</a></li>
        <li><a href="#studio" className="hover:underline">Studio</a></li>
        <li><a href="#journal" className="hover:underline">Journal</a></li>
      </ul>
    </nav>
  </header>
);

const Hero = () => (
  <section className="px-6 py-20 md:py-40 text-center animate-fade-in">
    <h2 className="hero-text mb-6">Form. Fabric. Future.</h2>
    <p className="text-lg md:text-2xl max-w-3xl mx-auto font-light text-gray-700 mb-10">
      A digital atelier redefining modern luxury through minimal brutalism and tactile elegance.
    </p>
    <button className="btn">Explore the Collection</button>
  </section>
);

const EditorialSection = () => (
  <section className="px-6 py-20 bg-soft-black text-off-white animate-slide-up">
    <div className="max-w-6xl mx-auto">
      <h2 className="section-title text-off-white">Editorial Vision</h2>
      <div className="grid md:grid-cols-2 gap-10 items-center">
        <div>
          <p className="text-lg leading-relaxed mb-6">
            Each season unfolds as a narrative — a convergence of architecture, emotion, and silhouette.
            We strip away excess to reveal the essence of form.
          </p>
          <p className="text-lg leading-relaxed">
            Shot in raw urban spaces and quiet interiors, our editorials blur the line between fashion and fine art.
          </p>
        </div>
        <div className="bg-gray-300 h-64 md:h-80 rounded-lg overflow-hidden shadow-2xl">
          <img src="https://via.placeholder.com/600x400" alt="Editorial" className="w-full h-full object-cover" />
        </div>
      </div>
    </div>
  </section>
);

const InteractiveLookbook = () => (
  <section className="px-6 py-20">
    <div className="max-w-6xl mx-auto">
      <h2 className="section-title">Interactive Lookbook</h2>
      <div className="grid md:grid-cols-3 gap-6">
        {[1, 2, 3].map((item) => (
          <div key={item} className="group cursor-pointer">
            <div className="bg-gray-200 h-60 rounded-lg mb-4 overflow-hidden shadow-md transition-transform duration-500 group-hover:scale-105">
              <img
                src={`https://via.placeholder.com/400x500/${item % 2 === 0 ? '000000' : 'f8f8f8'}/ffffff?text=Look+${item}`}
                alt={`Look ${item}`}
                className="w-full h-full object-cover"
              />
            </div>
            <h3 className="font-light text-lg">Look {item}</h3>
            <p className="text-sm text-gray-600">Silk, Wool, Recycled Metal</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const Footer = () => (
  <footer className="px-6 py-12 border-t border-warm-gray text-center text-sm text-gray-600">
    <p>&copy; {new Date().getFullYear()} MAISON NOIR. All rights reserved.</p>
    <p className="mt-2">Crafted with precision. Hosted in the cloud.</p>
  </footer>
);

export default App;