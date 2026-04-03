import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <section className="relative h-screen flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 z-0">
        <img
          src="https://source.unsplash.com/random/1920x1080/?fashion,runway,dark"
          alt="Runway"
          className="w-full h-full object-cover filter brightness-50"
        />
      </div>
      <div className="relative z-10 text-center px-6">
        <h2 className="text-6xl md:text-8xl font-light tracking-tight mb-4">AUTUMN/WINTER 2024</h2>
        <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
          A meditation on structure, silence, and the tension between minimalism and luxury.
        </p>
        <Link
          to="/collections"
          className="inline-block border border-white px-8 py-3 text-sm uppercase tracking-wider hover:bg-white hover:text-black transition"
        >
          Explore Collection
        </Link>
      </div>
    </section>
  );
};

export default HomePage;