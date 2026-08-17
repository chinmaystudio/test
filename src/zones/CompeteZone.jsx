import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Float, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useWorldStore } from '../store/worldStore';

export function CompeteZone() {
  const groupRef = useRef();
  const octahedronRef = useRef();
  const ringsRef = useRef();
  const particlesRef = useRef();

  // Hover states
  const setHoveredObject = useWorldStore((state) => state.setHoveredObject);

  // Generate particles
  const particleCount = 200;
  const positions = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const radius = 5 + Math.random() * 5;
      const theta = Math.random() * Math.PI * 2;
      pos[i * 3] = Math.cos(theta) * radius;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 20; // Height -10 to 10
      pos[i * 3 + 2] = Math.sin(theta) * radius;
    }
    return pos;
  }, [particleCount]);

  useFrame((state, delta) => {
    // Fast rotations for dynamic feel
    if (octahedronRef.current) {
      octahedronRef.current.rotation.x += delta * 0.5;
      octahedronRef.current.rotation.y += delta * 0.8;
      octahedronRef.current.rotation.z += delta * 0.3;
    }

    if (ringsRef.current) {
      ringsRef.current.children[0].rotation.x -= delta * 1.5;
      ringsRef.current.children[1].rotation.y += delta * 2.0;
      ringsRef.current.children[2].rotation.z -= delta * 1.2;
    }

    if (groupRef.current) {
      // Orbiting obstacles
      const time = state.clock.getElapsedTime();
      groupRef.current.children.forEach((child, i) => {
        if (child.userData.isObstacle) {
          child.position.x = Math.cos(time * child.userData.speed + i) * child.userData.radius;
          child.position.z = Math.sin(time * child.userData.speed + i) * child.userData.radius;
          child.rotation.x += delta * 2;
          child.rotation.y += delta * 2;
        }
      });
    }

    if (particlesRef.current) {
      const positions = particlesRef.current.geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        positions[i * 3 + 1] += delta * 5; // Move upward fast
        if (positions[i * 3 + 1] > 10) {
          positions[i * 3 + 1] = -10; // Recycle
        }
      }
      particlesRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  const obstacles = useMemo(() => [
    { type: 'box', radius: 8, speed: 0.8, height: 2 },
    { type: 'tetrahedron', radius: 10, speed: 0.5, height: -3 },
    { type: 'torus', radius: 12, speed: 0.6, height: 5 },
    { type: 'box', radius: 6, speed: -0.7, height: 4 },
    { type: 'tetrahedron', radius: 9, speed: -0.9, height: -2 },
  ], []);

  const markers = [
    { label: 'Hackathon', position: [4, 4, 4] },
    { label: 'CodeWars', position: [-4, 5, -4] },
    { label: 'Quiz', position: [5, -3, 3] },
    { label: 'E-Sports', position: [-5, -2, -5] },
  ];

  return (
    <group position={[35, 0, -60]}>
      {/* Lights */}
      <pointLight position={[0, 5, 0]} intensity={200} color="#ff6d00" distance={30} />
      <pointLight position={[5, -5, 5]} intensity={150} color="#f44336" distance={20} />

      {/* Central Octahedron */}
      <mesh ref={octahedronRef} scale={3}>
        <octahedronGeometry args={[1, 0]} />
        <meshStandardMaterial color="#ff6d00" wireframe emissive="#ff6d00" emissiveIntensity={0.5} />
      </mesh>

      {/* Countdown Rings */}
      <group ref={ringsRef}>
        <mesh>
          <torusGeometry args={[4, 0.05, 16, 100]} />
          <meshBasicMaterial color="#f44336" />
        </mesh>
        <mesh>
          <torusGeometry args={[4.5, 0.05, 16, 100]} />
          <meshBasicMaterial color="#ff6d00" />
        </mesh>
        <mesh>
          <torusGeometry args={[5, 0.05, 16, 100]} />
          <meshBasicMaterial color="#ffc107" />
        </mesh>
      </group>

      {/* Obstacles */}
      <group ref={groupRef}>
        {obstacles.map((obs, i) => {
          let Geom;
          if (obs.type === 'box') Geom = <boxGeometry args={[1, 1, 1]} />;
          else if (obs.type === 'tetrahedron') Geom = <tetrahedronGeometry args={[1, 0]} />;
          else Geom = <torusGeometry args={[0.8, 0.2, 16, 32]} />;

          return (
            <mesh 
              key={i} 
              position={[obs.radius, obs.height, 0]} 
              userData={{ isObstacle: true, radius: obs.radius, speed: obs.speed }}
            >
              {Geom}
              <meshStandardMaterial color="#ff9800" roughness={0.2} metalness={0.8} />
            </mesh>
          );
        })}
      </group>

      {/* Competition Markers */}
      {markers.map((marker, i) => (
        <Float key={i} speed={3} rotationIntensity={2} floatIntensity={3}>
          <group position={marker.position}>
            <mesh 
              onPointerOver={() => setHoveredObject(`compete-${marker.label}`)}
              onPointerOut={() => setHoveredObject(null)}
            >
              <boxGeometry args={[1, 1, 1]} />
              <meshStandardMaterial color="#f44336" emissive="#f44336" emissiveIntensity={0.2} />
            </mesh>
            <Text
              position={[0, 1.2, 0]}
              fontSize={0.8}
              color="#ffffff"
              outlineWidth={0.05}
              outlineColor="#000000"
            >
              {marker.label}
            </Text>
          </group>
        </Float>
      ))}

      {/* Particles */}
      <Points ref={particlesRef} positions={positions}>
        <PointMaterial transparent color="#ffc107" size={0.15} sizeAttenuation depthWrite={false} />
      </Points>
    </group>
  );
}
