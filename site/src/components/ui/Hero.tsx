import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface HeroProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  backgroundClass?: string;
  backgroundImage?: string;
}

export default function Hero({
  title,
  subtitle,
  children,
  backgroundClass = 'bg-gradient-to-b from-bg-primary to-bg-secondary',
  backgroundImage,
}: HeroProps) {
  const sectionStyle = backgroundImage
    ? {
      backgroundImage: `linear-gradient(to bottom, rgba(249, 250, 251, 0.5), rgba(243, 244, 246, 0.6)), url(${backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
    }
    : {};

  return (
    <section
      className={`min-h-screen flex items-center justify-center ${backgroundClass}`}
      style={sectionStyle}
    >
      <style>{`
        .hero-dark-overlay .btn-secondary {
          color: white !important;
          border-color: white !important;
          background-color: transparent !important;
        }
        .hero-dark-overlay .btn-secondary:hover {
          background-color: white !important;
          color: rgba(0, 0, 0, 0.9) !important;
          border-color: white !important;
        }
      `}</style>
      <div className="container-custom text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="hero-dark-overlay inline-block px-8 py-12 md:px-12 md:py-16 rounded-2xl backdrop-blur-md"
          style={{
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          }}
        >
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-4xl md:text-6xl font-bold text-white mb-6"
          >
            {title}
          </motion.h1>

          {subtitle && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl md:text-2xl text-gray-100 mb-8 max-w-2xl mx-auto"
            >
              {subtitle}
            </motion.p>
          )}

          {children && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              {children}
            </motion.div>
          )}
        </motion.div>
      </div>
    </section>
  );
}
