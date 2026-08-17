import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import NavObject from './NavObject';

export default function SpatialNav() {
  const groupRef = useRef();

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.1;
    }
  });

  const radius = 12;
  const height = 3;

  const navItems = [
    { zone: 'EVENTS', color: '#ff0055', label: 'Events', geometryType: 'torus' },
    { zone: 'PROJECTS', color: '#00ffcc', label: 'Projects', geometryType: 'octahedron' },
    { zone: 'COMMUNITY', color: '#ffcc00', label: 'Community', geometryType: 'icosahedron' },
    { zone: 'COMPETE', color: '#cc00ff', label: 'Compete', geometryType: 'dodecahedron' },
    { zone: 'LEARN', color: '#0055ff', label: 'Learn', geometryType: 'stack' },
  ];

  return (
    <group ref={groupRef}>
      {navItems.map((item, index) => {
        const angle = (index / navItems.length) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;

        return (
          <NavObject
            key={item.zone}
            zone={item.zone}
            color={item.color}
            label={item.label}
            geometryType={item.geometryType}
            position={[x, height, z]}
          />
        );
      })}
    </group>
  );
}
