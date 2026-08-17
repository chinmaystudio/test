import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Text } from '@react-three/drei';
import { useWorldStore } from '../store/worldStore';
import * as THREE from 'three';

export default function NavObject({ zone, color, position, geometryType, label }) {
  const meshRef = useRef();
  const setZone = useWorldStore((state) => state.setZone);
  const currentZone = useWorldStore((state) => state.currentZone);
  const [hovered, setHovered] = useState(false);

  const isSelected = currentZone === zone;

  const handlePointerEnter = () => {
    setHovered(true);
    document.body.style.cursor = 'pointer';
  };

  const handlePointerLeave = () => {
    setHovered(false);
    document.body.style.cursor = 'auto';
  };

  const handleClick = (e) => {
    e.stopPropagation();
    setZone(zone);
  };

  useFrame((state, delta) => {
    if (!meshRef.current) return;
    
    // Scale animation
    const targetScale = hovered || isSelected ? 1.3 : 1.0;
    meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), delta * 5);
    
    // Emissive animation
    const targetEmissiveIntensity = hovered || isSelected ? 2.0 : 0.5;
    if (meshRef.current.material) {
      meshRef.current.material.emissiveIntensity = THREE.MathUtils.lerp(
        meshRef.current.material.emissiveIntensity,
        targetEmissiveIntensity,
        delta * 5
      );
    } else if (meshRef.current.children) {
      meshRef.current.children.forEach(child => {
        if (child.material) {
           child.material.emissiveIntensity = THREE.MathUtils.lerp(
             child.material.emissiveIntensity,
             targetEmissiveIntensity,
             delta * 5
           );
        }
      });
    }
  });

  const renderGeometry = () => {
    switch (geometryType) {
      case 'torus':
        return <torusGeometry args={[1, 0.3, 16, 32]} />;
      case 'octahedron':
        return <octahedronGeometry args={[1, 0]} />;
      case 'icosahedron':
        return <icosahedronGeometry args={[1, 1]} />;
      case 'dodecahedron':
        return <dodecahedronGeometry args={[1, 0]} />;
      case 'stack':
        return (
          <>
            <mesh position={[0, -0.6, 0]}>
              <boxGeometry args={[0.8, 0.4, 0.8]} />
              <meshPhysicalMaterial color={color} emissive={color} emissiveIntensity={isSelected ? 2 : 0.5} roughness={0.2} metalness={0.8} />
            </mesh>
            <mesh position={[0, 0, 0]}>
              <boxGeometry args={[0.8, 0.4, 0.8]} />
              <meshPhysicalMaterial color={color} emissive={color} emissiveIntensity={isSelected ? 2 : 0.5} roughness={0.2} metalness={0.8} />
            </mesh>
            <mesh position={[0, 0.6, 0]}>
              <boxGeometry args={[0.8, 0.4, 0.8]} />
              <meshPhysicalMaterial color={color} emissive={color} emissiveIntensity={isSelected ? 2 : 0.5} roughness={0.2} metalness={0.8} />
            </mesh>
          </>
        );
      default:
        return <boxGeometry args={[1, 1, 1]} />;
    }
  };

  return (
    <group position={position}>
      <Float speed={2} rotationIntensity={1} floatIntensity={1}>
        {geometryType === 'stack' ? (
          <group 
            ref={meshRef}
            onPointerEnter={handlePointerEnter}
            onPointerLeave={handlePointerLeave}
            onClick={handleClick}
          >
            {renderGeometry()}
          </group>
        ) : (
          <mesh
            ref={meshRef}
            onPointerEnter={handlePointerEnter}
            onPointerLeave={handlePointerLeave}
            onClick={handleClick}
          >
            {renderGeometry()}
            <meshPhysicalMaterial 
              color={color} 
              emissive={color} 
              emissiveIntensity={isSelected ? 2 : 0.5} 
              roughness={0.2} 
              metalness={0.8}
              wireframe={geometryType === 'icosahedron'}
            />
          </mesh>
        )}
      </Float>
      <Text
        position={[0, -2, 0]}
        fontSize={0.4}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
    </group>
  );
}
