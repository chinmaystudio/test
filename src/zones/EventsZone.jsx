import React, { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text, Float, Line } from '@react-three/drei'
import * as THREE from 'three'
import { useWorldStore } from '../store/worldStore'
import events from '../data/events'

export default function EventsZone() {
  const groupRef = useRef()
  const ringRef = useRef()

  useFrame((state, delta) => {
    if (ringRef.current) {
      ringRef.current.rotation.y += delta * 0.1
    }
  })

  // 8 screens in a circular arena
  const numScreens = 8
  const radius = 10

  return (
    <group position={[45, 0, -10]} ref={groupRef}>
      <pointLight position={[0, 5, 0]} color="#00e5ff" intensity={2} distance={30} />
      
      {/* Circular Arena */}
      <group ref={ringRef}>
        {Array.from({ length: numScreens }).map((_, i) => {
          const angle = (i / numScreens) * Math.PI * 2
          const x = Math.cos(angle) * radius
          const z = Math.sin(angle) * radius
          return (
            <mesh key={i} position={[x, 3, z]} rotation={[0, -angle + Math.PI/2, 0.1]}>
              <planeGeometry args={[3, 4]} />
              <meshBasicMaterial color="#00e5ff" wireframe opacity={0.2} transparent />
            </mesh>
          )
        })}
      </group>

      {/* 3D Timeline Path */}
      <group position={[0, 3, 0]}>
        <mesh position={[-6, 0, 0]}>
          <sphereGeometry args={[0.6, 16, 16]} />
          <meshStandardMaterial color="#555555" emissive="#555555" emissiveIntensity={0.5} />
          <Text position={[0, -1.2, 0]} fontSize={0.5} color="white">PAST</Text>
        </mesh>
        
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[0.8, 16, 16]} />
          <meshStandardMaterial color="#00e5ff" emissive="#00e5ff" emissiveIntensity={1} />
          <Text position={[0, -1.5, 0]} fontSize={0.6} color="white">CURRENT</Text>
        </mesh>

        <mesh position={[6, 0, 0]}>
          <sphereGeometry args={[0.6, 16, 16]} />
          <meshStandardMaterial color="#00ffcc" emissive="#00ffcc" emissiveIntensity={0.8} />
          <Text position={[0, -1.2, 0]} fontSize={0.5} color="white">NEXT</Text>
        </mesh>
        
        <Line points={[[-6, 0, 0], [6, 0, 0]]} color="#00e5ff" lineWidth={2} transparent opacity={0.6} />
      </group>

      {/* Event Nodes */}
      <group position={[0, 8, 0]}>
        {events && events.map((event, i) => {
          const isPraxis = event.name && event.name.toUpperCase().includes('PRAXIS 2026')
          const scale = isPraxis ? 2 : 1
          
          // Spread them around the arena randomly or circularly
          const angle = (i / events.length) * Math.PI * 2
          const nodeRadius = 6
          const x = Math.cos(angle) * nodeRadius
          const z = Math.sin(angle) * nodeRadius
          const y = (i % 3) * 2 - 2

          return (
            <Float key={`event-${i}`} speed={2} rotationIntensity={0.5} floatIntensity={1}>
              <mesh position={[x, y, z]}>
                <sphereGeometry args={[0.4 * scale, 16, 16]} />
                <meshStandardMaterial color="#ff00e5" emissive="#ff00e5" emissiveIntensity={1.5} />
                <Text position={[0, -1 * scale, 0]} fontSize={0.5} color="white">
                  {event.name || `Event ${i+1}`}
                </Text>
              </mesh>
            </Float>
          )
        })}
      </group>
    </group>
  )
}
