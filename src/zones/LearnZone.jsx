import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Float, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useWorldStore } from '../store/worldStore';

export function LearnZone() {
  const groupRef = useRef();
  const setHoveredObject = useWorldStore((state) => state.setHoveredObject);

  const platforms = [
    { topic: 'Programming', height: 0, color: '#00d4ff' },
    { topic: 'Web Dev', height: 5, color: '#00e5ff' },
    { topic: 'AI & ML', height: 10, color: '#00e676' },
    { topic: 'Data Science', height: 15, color: '#76ff03' },
    { topic: 'Cloud Computing', height: 20, color: '#ffd600' },
    { topic: 'Gen AI', height: 25, color: '#ffab00' },
  ];

  // Particles around platforms
  const particleCount = 300;
  const particlesRef = useRef();
  
  const particlePositions = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const radius = 3 + Math.random() * 4;
      const theta = Math.random() * Math.PI * 2;
      const y = Math.random() * 30 - 2; // Range -2 to 28
      pos[i * 3] = Math.cos(theta) * radius;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = Math.sin(theta) * radius;
    }
    return pos;
  }, [particleCount]);

  useFrame((state, delta) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y += delta * 0.1;
    }
    
    if (groupRef.current) {
      // Gentle rotation for the whole tower structure
      groupRef.current.rotation.y = Math.sin(state.clock.getElapsedTime() * 0.2) * 0.1;
    }
  });

  return (
    <group position={[-35, 0, 20]} ref={groupRef}>
      {/* Vertical beam of light */}
      <mesh position={[0, 12.5, 0]}>
        <cylinderGeometry args={[0.2, 0.2, 30, 8]} />
        <meshBasicMaterial color="#ffffff" transparent opacity={0.5} />
      </mesh>

      {/* Platforms */}
      {platforms.map((plat, i) => (
        <group key={i} position={[0, plat.height, 0]}>
          <Float speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
            <mesh 
              onPointerOver={() => setHoveredObject(`learn-${plat.topic}`)}
              onPointerOut={() => setHoveredObject(null)}
            >
              <cylinderGeometry args={[4, 4, 0.5, 6]} />
              <meshStandardMaterial 
                color={plat.color} 
                transparent 
                opacity={0.8} 
                metalness={0.5} 
                roughness={0.2}
                emissive={plat.color}
                emissiveIntensity={0.2}
              />
            </mesh>
            <Text
              position={[0, 1.5, 3]}
              fontSize={0.8}
              color="#ffffff"
              outlineWidth={0.05}
              outlineColor="#000000"
            >
              {plat.topic}
            </Text>
          </Float>

          {/* Connection line to next platform if not last */}
          {i < platforms.length - 1 && (
            <mesh position={[2, 2.5, 2]} rotation={[0, 0, Math.PI / 8]}>
              <cylinderGeometry args={[0.05, 0.05, 5.5, 4]} />
              <meshBasicMaterial color={platforms[i+1].color} transparent opacity={0.6} />
            </mesh>
          )}
        </group>
      ))}

      {/* Orbiting particles */}
      <Points ref={particlesRef} positions={particlePositions}>
        <PointMaterial transparent color="#00e5ff" size={0.08} sizeAttenuation depthWrite={false} />
      </Points>

      {/* Lighting */}
      <pointLight position={[0, -5, 0]} intensity={100} color="#00d4ff" distance={30} />
      <pointLight position={[0, 30, 0]} intensity={100} color="#ffab00" distance={30} />
      <ambientLight intensity={0.5} />
    </group>
  );
}
