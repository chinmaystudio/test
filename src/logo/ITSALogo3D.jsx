import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Float } from '@react-three/drei';
import * as THREE from 'three';

export default function ITSALogo3D() {
  const groupRef = useRef();
  const glowRef = useRef();

  const letterGeometries = useMemo(() => {
    const letters = ['I', 'T', 'S', 'A'];
    const spacing = 2.2;
    const startX = -((letters.length - 1) * spacing) / 2;

    return letters.map((letter, i) => ({
      letter,
      position: [startX + i * spacing, 0, 0],
    }));
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
      groupRef.current.position.y = 8 + Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
    }
    if (glowRef.current) {
      glowRef.current.material.emissiveIntensity = 0.5 + Math.sin(state.clock.elapsedTime * 2) * 0.2;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.1} floatIntensity={0.3}>
      <group ref={groupRef} position={[0, 8, 0]}>
        {letterGeometries.map(({ letter, position }, i) => (
          <group key={letter + i} position={position}>
            {/* Main 3D letter */}
            <mesh castShadow>
              <boxGeometry args={[1.5, 2, 0.6]} />
              <meshPhysicalMaterial
                color="#0a1628"
                metalness={0.9}
                roughness={0.1}
                clearcoat={1}
                clearcoatRoughness={0.1}
                envMapIntensity={2}
                emissive="#00d4ff"
                emissiveIntensity={0.15}
              />
            </mesh>

            {/* Letter face */}
            <Text
              position={[0, 0, 0.32]}
              fontSize={1.4}
              font={undefined}
              color="#00d4ff"
              anchorX="center"
              anchorY="middle"
              outlineWidth={0.02}
              outlineColor="#ffffff"
            >
              {letter}
            </Text>

            {/* Back face */}
            <Text
              position={[0, 0, -0.32]}
              fontSize={1.4}
              font={undefined}
              color="#aa00ff"
              anchorX="center"
              anchorY="middle"
              rotation={[0, Math.PI, 0]}
            >
              {letter}
            </Text>

            {/* Edge glow */}
            <mesh ref={i === 0 ? glowRef : undefined}>
              <boxGeometry args={[1.6, 2.1, 0.7]} />
              <meshStandardMaterial
                color="#00d4ff"
                emissive="#00d4ff"
                emissiveIntensity={0.3}
                transparent
                opacity={0.08}
                side={THREE.BackSide}
              />
            </mesh>
          </group>
        ))}

        {/* Subtitle */}
        <Text
          position={[0, -1.8, 0]}
          fontSize={0.35}
          color="#ffffff"
          anchorX="center"
          anchorY="middle"
          letterSpacing={0.35}
          opacity={0.5}
        >
          DIGITAL NEXUS
        </Text>

        {/* Accent line */}
        <mesh position={[0, -1.3, 0]}>
          <boxGeometry args={[8, 0.02, 0.02]} />
          <meshStandardMaterial
            color="#00d4ff"
            emissive="#00d4ff"
            emissiveIntensity={1}
          />
        </mesh>
      </group>
    </Float>
  );
}
