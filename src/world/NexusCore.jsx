import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Torus } from '@react-three/drei';
import * as THREE from 'three';
import { useWorldStore } from '../store/worldStore';

export default function NexusCore() {
  const coreRef = useRef();
  const innerRef = useRef();

  // Custom noisy icosahedron
  const geometry = useMemo(() => {
    const geo = new THREE.IcosahedronGeometry(6, 2);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const v = new THREE.Vector3().fromBufferAttribute(pos, i);
      v.add(v.clone().normalize().multiplyScalar(Math.random() * 0.5));
      pos.setXYZ(i, v.x, v.y, v.z);
    }
    geo.computeVertexNormals();
    return geo;
  }, []);

  const fragments = useMemo(() => {
    const frags = [];
    for (let i = 0; i < 25; i++) {
      frags.push({
        position: [
          (Math.random() - 0.5) * 20,
          (Math.random() - 0.5) * 15,
          (Math.random() - 0.5) * 20,
        ],
        scale: Math.random() * 0.5 + 0.2,
        rotation: [Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI],
        speed: Math.random() * 0.2 + 0.1,
      });
    }
    return frags;
  }, []);

  useFrame((state, delta) => {
    const t = state.clock.getElapsedTime();
    if (coreRef.current) {
      coreRef.current.rotation.y += delta * 0.1;
      const scale = 1 + Math.sin(t * 1.5) * 0.05;
      coreRef.current.scale.set(scale, scale, scale);
    }
    if (innerRef.current) {
      innerRef.current.rotation.y -= delta * 0.2;
    }
  });

  return (
    <group ref={coreRef}>
      {/* Main Structure */}
      <mesh geometry={geometry}>
        <meshPhysicalMaterial 
          color="#00d4ff" 
          metalness={0.1} 
          roughness={0.05} 
          transmission={0.6} 
          thickness={1.5} 
          transparent
        />
      </mesh>
      
      {/* Wireframe overlay */}
      <mesh geometry={geometry}>
        <meshBasicMaterial color="#00ffff" wireframe transparent opacity={0.3} />
      </mesh>

      {/* Inner Emissive Core */}
      <mesh ref={innerRef}>
        <sphereGeometry args={[4, 32, 32]} />
        <meshStandardMaterial color="#00ffff" emissive="#00ffff" emissiveIntensity={2} toneMapped={false} />
      </mesh>

      {/* Orbiting Rings */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <Torus args={[9, 0.05, 16, 100]} rotation={[Math.PI / 2.5, 0, 0]}>
          <meshStandardMaterial color="#00d4ff" emissive="#00d4ff" emissiveIntensity={1} />
        </Torus>
      </Float>
      <Float speed={1.5} rotationIntensity={0.8} floatIntensity={0.8}>
        <Torus args={[10, 0.05, 16, 100]} rotation={[-Math.PI / 4, Math.PI / 4, 0]}>
          <meshStandardMaterial color="#00d4ff" emissive="#00d4ff" emissiveIntensity={1.5} />
        </Torus>
      </Float>
      <Float speed={2.5} rotationIntensity={0.6} floatIntensity={0.6}>
        <Torus args={[11, 0.05, 16, 100]} rotation={[0, Math.PI / 3, Math.PI / 6]}>
          <meshStandardMaterial color="#00d4ff" emissive="#00d4ff" emissiveIntensity={0.5} />
        </Torus>
      </Float>

      {/* Floating Fragments */}
      {fragments.map((frag, i) => (
        <Float key={i} speed={frag.speed * 5} rotationIntensity={2} floatIntensity={2} position={frag.position}>
          <mesh rotation={frag.rotation} scale={frag.scale}>
            <octahedronGeometry args={[1, 0]} />
            <meshPhysicalMaterial 
              color="#00d4ff" 
              metalness={0.2} 
              roughness={0.1} 
              transmission={0.8}
              thickness={0.5}
            />
          </mesh>
        </Float>
      ))}

      {/* Glowing Nodes */}
      {fragments.slice(0, 10).map((frag, i) => (
        <Float key={`node-${i}`} speed={frag.speed * 3} position={[frag.position[0] * 0.8, frag.position[1] * 0.8, frag.position[2] * 0.8]}>
          <mesh>
            <sphereGeometry args={[0.15, 16, 16]} />
            <meshBasicMaterial color="#ffffff" />
          </mesh>
        </Float>
      ))}
    </group>
  );
}
