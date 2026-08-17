import React, { useState, useEffect, useCallback } from 'react';
import { useWorldStore } from '../store/worldStore';

export default function LoadingScreen() {
  const isLoading = useWorldStore((s) => s.isLoading);
  const [progress, setProgress] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [particles, setParticles] = useState([]);

  // Generate loading particles
  useEffect(() => {
    const pts = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 1 + Math.random() * 3,
      speed: 0.5 + Math.random() * 2,
      delay: Math.random() * 2,
      opacity: 0.1 + Math.random() * 0.4,
    }));
    setParticles(pts);
  }, []);

  // Simulate loading progress
  useEffect(() => {
    let interval;
    if (!loaded) {
      interval = setInterval(() => {
        setProgress((prev) => {
          const next = prev + Math.random() * 15;
          if (next >= 100) {
            clearInterval(interval);
            setTimeout(() => {
              setLoaded(true);
              useWorldStore.getState().setLoading(false);
            }, 800);
            return 100;
          }
          return next;
        });
      }, 200);
    }
    return () => clearInterval(interval);
  }, [loaded]);

  return (
    <div className={`loading-screen ${loaded ? 'loaded' : ''}`}>
      {/* Animated background particles */}
      <svg
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          opacity: 0.3,
        }}
      >
        {particles.map((p) => (
          <circle
            key={p.id}
            cx={`${p.x}%`}
            cy={`${p.y}%`}
            r={p.size}
            fill="#00d4ff"
            opacity={p.opacity}
          >
            <animate
              attributeName="cy"
              from={`${p.y}%`}
              to={`${p.y - 20}%`}
              dur={`${p.speed}s`}
              begin={`${p.delay}s`}
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values={`${p.opacity};${p.opacity * 2};${p.opacity}`}
              dur={`${p.speed * 1.5}s`}
              begin={`${p.delay}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}

        {/* Connection lines */}
        {particles.slice(0, 15).map((p, i) => {
          const next = particles[(i + 1) % 15];
          return (
            <line
              key={`line-${i}`}
              x1={`${p.x}%`}
              y1={`${p.y}%`}
              x2={`${next.x}%`}
              y2={`${next.y}%`}
              stroke="#00d4ff"
              strokeWidth="0.5"
              opacity={0.05 + (progress / 100) * 0.1}
            >
              <animate
                attributeName="opacity"
                values={`0.02;${0.05 + (progress / 100) * 0.15};0.02`}
                dur="3s"
                repeatCount="indefinite"
              />
            </line>
          );
        })}
      </svg>

      {/* Logo */}
      <div className="loading-title">ITSA</div>
      <div className="loading-subtitle">Digital Nexus</div>

      {/* Progress bar */}
      <div className="loading-bar-container">
        <div
          className="loading-bar"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      <div className="loading-progress-text">
        {progress < 100
          ? `INITIALIZING WORLD — ${Math.floor(progress)}%`
          : 'ENTERING NEXUS'}
      </div>
    </div>
  );
}
