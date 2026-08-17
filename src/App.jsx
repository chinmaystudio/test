import React, { Suspense, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { AdaptiveDpr, Preload } from '@react-three/drei';
import { useWorldStore } from './store/worldStore';

// 3D World
import NexusCore from './world/NexusCore';
import Environment3D from './world/Environment3D';
import WorldGrid from './world/WorldGrid';
import Particles from './world/Particles';

// Camera
import CameraController from './camera/CameraController';

// Navigation
import SpatialNav from './navigation/SpatialNav';

// Logo
import ITSALogo3D from './logo/ITSALogo3D';

// Zones
import EventsZone from './zones/EventsZone';
import ProjectsZone from './zones/ProjectsZone';
import CommunityZone from './zones/CommunityZone';
import CompeteZone from './zones/CompeteZone';
import LearnZone from './zones/LearnZone';
import AboutZone from './zones/AboutZone';
import ContactZone from './zones/ContactZone';
import PeopleNetwork from './zones/PeopleNetwork';

// Effects
import PostProcessing from './effects/PostProcessing';

// HTML
import HtmlOverlay from './overlay/HtmlOverlay';
import LoadingScreen from './loading/LoadingScreen';

function Scene() {
  return (
    <>
      {/* Global environment */}
      <Environment3D />
      <WorldGrid />
      <Particles />

      {/* Camera control */}
      <CameraController />

      {/* Central structure */}
      <NexusCore />
      <ITSALogo3D />

      {/* Spatial navigation */}
      <SpatialNav />

      {/* Zone environments — always present in the world */}
      <EventsZone />
      <ProjectsZone />
      <CommunityZone />
      <CompeteZone />
      <LearnZone />
      <AboutZone />
      <ContactZone />
      <PeopleNetwork />

      {/* Post-processing */}
      <PostProcessing />

      {/* Preload assets */}
      <Preload all />
    </>
  );
}

export default function App() {
  const isLoading = useWorldStore((s) => s.isLoading);

  // Set document title
  useEffect(() => {
    document.title = 'ITSA Digital Nexus — Information Technology Students Association, PCCOE';

    // Add meta description
    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'description';
      document.head.appendChild(meta);
    }
    meta.content = 'Explore ITSA — the Information Technology Students Association at PCCOE, Pune — through an immersive 3D digital world. Events, projects, communities, learning, and more.';
  }, []);

  return (
    <>
      {/* Loading screen */}
      <LoadingScreen />

      {/* Main 3D Canvas */}
      <div className="canvas-container">
        <Canvas
          camera={{
            position: [0, 3, 18],
            fov: 60,
            near: 0.1,
            far: 500,
          }}
          dpr={[1, 2]}
          gl={{
            antialias: true,
            alpha: false,
            powerPreference: 'high-performance',
            stencil: false,
          }}
          shadows={false}
          style={{ background: '#050510' }}
        >
          <Suspense fallback={null}>
            <Scene />
          </Suspense>
          <AdaptiveDpr pixelated />
        </Canvas>
      </div>

      {/* HTML Overlay */}
      {!isLoading && <HtmlOverlay />}
    </>
  );
}
