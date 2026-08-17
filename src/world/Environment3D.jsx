import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWorldStore } from '../store/worldStore';

const FOG_COLORS = {
  NEXUS: '#050510',
  EVENTS: '#050815',
  PROJECTS: '#0a0515',
  COMMUNITY: '#050a08',
  COMPETE: '#100805',
  LEARN: '#0a0a05',
  ABOUT: '#080808',
  CONTACT: '#0a0308',
  PEOPLE: '#050510'
};

export default function Environment3D() {
  const currentZone = useWorldStore((state) => state.currentZone);
  const fogRef = useRef();
  const light1Ref = useRef();
  const light2Ref = useRef();
  const targetColor = new THREE.Color();

  useFrame((state, delta) => {
    const t = state.clock.getElapsedTime();
    
    // Animate lights
    if (light1Ref.current) {
      light1Ref.current.position.set(
        Math.cos(t * 0.5) * 20,
        Math.sin(t * 0.3) * 10 + 5,
        Math.sin(t * 0.5) * 20
      );
    }
    if (light2Ref.current) {
      light2Ref.current.position.set(
        Math.sin(t * 0.4) * 25,
        Math.cos(t * 0.6) * 15,
        Math.cos(t * 0.4) * 25
      );
    }

    // Lerp fog color
    if (fogRef.current) {
      targetColor.set(FOG_COLORS[currentZone] || FOG_COLORS.NEXUS);
      fogRef.current.color.lerp(targetColor, delta * 2);
    }
  });

  return (
    <>
      <fog ref={fogRef} attach="fog" args={['#050510', 10, 100]} />
      <Stars radius={300} depth={60} count={3000} factor={4} saturation={0} fade speed={1} />
      
      <ambientLight intensity={0.15} />
      
      <pointLight ref={light1Ref} color="#00ffff" intensity={2} distance={50} />
      <pointLight ref={light2Ref} color="#ff00ff" intensity={1.5} distance={50} />
    </>
  );
}
