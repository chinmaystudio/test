import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text, Line, Float } from '@react-three/drei'
import * as THREE from 'three'
import { useWorldStore } from '../store/worldStore'
import { domainNodes, communities } from '../data/communities'

export default function CommunityZone() {
  const groupRef = useRef()

  // Slow pulsing for network
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 1.5
    }
  })

  const connections = useMemo(() => {
    const lines = []
    if (domainNodes) {
      domainNodes.forEach((nodeA) => {
        if (nodeA.connectedTo) {
          nodeA.connectedTo.forEach((targetId) => {
            const nodeB = domainNodes.find(n => n.id === targetId)
            if (nodeB) {
              lines.push({ start: nodeA.position, end: nodeB.position, color: nodeA.color })
            }
          })
        }
      })
    }
    return lines
  }, [])

  return (
    <group position={[0, 0, -65]}>
      {/* Domain Network */}
      <group ref={groupRef}>
        {connections.map((conn, i) => (
          <Line 
            key={`conn-${i}`}
            points={[conn.start, conn.end]} 
            color={conn.color || '#00e5ff'} 
            lineWidth={2} 
            transparent 
            opacity={0.4} 
          />
        ))}

        {domainNodes && domainNodes.map((node, i) => (
          <group key={`node-${i}`} position={node.position}>
            <mesh>
              <sphereGeometry args={[0.8, 32, 32]} />
              <meshStandardMaterial 
                color={node.color || '#00e5ff'} 
                emissive={node.color || '#00e5ff'} 
                emissiveIntensity={2}
              />
            </mesh>
            <Text position={[0, -1.5, 0]} fontSize={0.5} color="white">
              {node.name}
            </Text>
          </group>
        ))}
      </group>

      {/* Community Chapters Ring Below */}
      <group position={[0, -10, 0]}>
        {communities && communities.map((comm, i) => {
          const angle = (i / communities.length) * Math.PI * 2
          const radius = 20
          const x = Math.cos(angle) * radius
          const z = Math.sin(angle) * radius
          return (
            <Float key={`comm-${i}`} position={[x, 0, z]} speed={2} rotationIntensity={0.5} floatIntensity={1}>
              <mesh>
                <boxGeometry args={[3, 3, 3]} />
                <meshStandardMaterial color={comm.color || '#333'} wireframe />
                <Text position={[0, -2.5, 0]} fontSize={0.6} color="white">
                  {comm.name}
                </Text>
              </mesh>
            </Float>
          )
        })}
      </group>
    </group>
  )
}
