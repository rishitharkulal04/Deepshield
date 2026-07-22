import { useState, useEffect } from 'react';
import '../styles/loader.css';

export default function LoaderScreen({ onComplete }) {
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!loading) {
      const timer = setTimeout(() => {
        onComplete?.();
      }, 500);
      return () => clearTimeout(timer);
    }

    // Simulate loading with varying speed
    const intervals = [];
    let currentProgress = 0;

    // Slow start
    intervals.push(
      setInterval(() => {
        setProgress(prev => {
          if (prev < 30) {
            currentProgress = prev + Math.random() * 8;
          } else if (prev < 70) {
            currentProgress = prev + Math.random() * 4;
          } else if (prev < 95) {
            currentProgress = prev + Math.random() * 1;
          } else {
            currentProgress = 98;
          }
          return Math.min(currentProgress, 98);
        });
      }, 200)
    );

    // Complete loading after 3 seconds
    const completeTimer = setTimeout(() => {
      setProgress(100);
      setLoading(false);
    }, 3000);

    return () => {
      intervals.forEach(interval => clearInterval(interval));
      clearTimeout(completeTimer);
    };
  }, [loading, onComplete]);

  if (!loading && progress === 100) {
    return null;
  }

  return (
    <div className={`loader-screen ${progress === 100 ? 'fade-out' : ''}`}>
      <div className="loader-container">
        <div className="loader-content">
          <div className="loader-logo">
            <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M30 2L50 10V30L30 50L10 30V10L30 2Z" stroke="currentColor" strokeWidth="1.5" fill="none" />
              <path d="M30 15L42 22V38L30 45L18 38V22L30 15Z" stroke="currentColor" strokeWidth="1.5" fill="none" opacity="0.5" />
            </svg>
          </div>
          
          <h1 className="loader-title">DeepShield</h1>
          <p className="loader-subtitle">Initializing Engine...</p>
          
          <div className="loader-progress-bar">
            <div className="loader-progress-fill" style={{ width: `${progress}%` }} />
          </div>
          
          <p className="loader-status">{Math.floor(progress)}%</p>
        </div>

        <div className="loader-grid" />
      </div>
    </div>
  );
}
