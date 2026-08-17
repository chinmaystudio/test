import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Line, Float } from '@react-three/drei';
import * as THREE from 'three';
import { useWorldStore } from '../store/worldStore';
import { itsaTeam } from '../data/itsaTeam';

export function PeopleNetwork() {
  const groupRef = useRef();
  const setHoveredObject = useWorldStore((state) => state.setHoveredObject);
  const hoveredObject = useWorldStore((state) => state.hoveredObject);

  const facultyNodes = itsaTeam.faculty || [];
  const coreNodes = itsaTeam.coreTeam || [];

  // Generate positions for nodes
  const nodes = useMemo(() => {
    const list = [];
    
    // Center node (ITSA)
    list.push({
      id: 'node-itsa',
      type: 'center',
      name: 'ITSA',
      role: 'Student Association',
      color: '#00d4ff',
      pos: [0, 0, 0],
      radius: 2,
    });

    // Faculty nodes (orbiting close)
    facultyNodes.forEach((faculty, i) => {
      const angle = (i / facultyNodes.length) * Math.PI * 2;
      const r = 6;
      list.push({
        id: `faculty-${i}`,
        type: 'faculty',
        name: faculty.name,
        role: faculty.role,
        color: '#ff6d00',
        pos: [Math.cos(angle) * r, 2 + Math.sin(angle) * 1, Math.sin(angle) * r],
        radius: 1,
        connectedTo: 'node-itsa',
      });
    });

    // Core team nodes (orbiting further)
    coreNodes.forEach((member, i) => {
      const angle = (i / coreNodes.length) * Math.PI * 2;
      const r = 12;
      list.push({
        id: `core-${i}`,
        type: 'core',
        name: member.name,
        role: member.role,
        color: member.color || '#e040fb',
        pos: [Math.cos(angle) * r, (Math.random() - 0.5) * 8, Math.sin(angle) * r],
        radius: 0.8,
        connectedTo: 'node-itsa',
      });
    });

    return list;
  }, [facultyNodes, coreNodes]);

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Gentle rotation of the entire network
      groupRef.current.rotation.y += delta * 0.05;
    }
  });

  return (
    <group position={[55, 0, 15]} ref={groupRef}>
      {/* Draw connections */}
      {nodes.map((node) => {
        if (!node.connectedTo) return null;
        const targetNode = nodes.find(n => n.id === node.connectedTo);
        if (!targetNode) return null;
        
        const isHovered = hoveredObject === node.id || hoveredObject === targetNode.id;
        
        return (
          <Line
            key={`line-${node.id}`}
            points={[node.pos, targetNode.pos]}
            color={isHovered ? '#ffffff' : node.color}
            lineWidth={isHovered ? 3 : 1}
            transparent
            opacity={isHovered ? 0.8 : 0.3}
          />
        );
      })}

      {/* Draw nodes */}
      {nodes.map((node) => {
        const isHovered = hoveredObject === node.id;
        
        return (
          <Float key={node.id} speed={2} rotationIntensity={0.5} floatIntensity={1}>
            <group position={node.pos}>
              <mesh
                onPointerOver={(e) => { e.stopPropagation(); setHoveredObject(node.id); }}
                onPointerOut={(e) => { e.stopPropagation(); setHoveredObject(null); }}
              >
                <sphereGeometry args={[node.radius, 32, 32]} />
                <meshStandardMaterial 
                  color={node.color} 
                  emissive={node.color}
                  emissiveIntensity={isHovered ? 1 : 0.2}
                  roughness={0.2}
                  metalness={0.8}
                />
              </mesh>
              
              {/* Text labels */}
              <Text
                position={[0, node.radius + 0.8, 0]}
                fontSize={isHovered ? 0.8 : 0.6}
                color="#ffffff"
                outlineWidth={0.05}
                outlineColor="#000000"
              >
                {node.name}
              </Text>
              {(isHovered || node.type === 'center') && (
                <Text
                  position={[0, node.radius + 0.2, 0]}
                  fontSize={0.4}
                  color={node.color}
                  outlineWidth={0.02}
                  outlineColor="#000000"
                >
                  {node.role}
                </Text>
              )}
            </group>
          </Float>
        );
      })}

      <pointLight position={[0, 5, 0]} intensity={150} color="#ffffff" distance={30} />
      <ambientLight intensity={0.4} />
    </group>
  );
}
