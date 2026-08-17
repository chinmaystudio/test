import React, { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text, Float, Sparkles } from '@react-three/drei'
import * as THREE from 'three'
import { useWorldStore } from '../store/worldStore'

export default function AboutZone() {
  const pillarsRef = useRef()

  useFrame((state, delta) => {
    if (pillarsRef.current) {
      pillarsRef.current.rotation.y += delta * 0.05
    }
  })

  const numPillars = 6
  const pillarRadius = 25

  return (
    <group position={[0, 0, 45]}>
      <Sparkles count={300} scale={50} size={3} speed={0.2} opacity={0.15} color="#e0ffff" />
      
      {/* Tall Thin Pillars */}
      <group ref={pillarsRef}>
        {Array.from({ length: numPillars }).map((_, i) => {
          const angle = (i / numPillars) * Math.PI * 2
          const x = Math.cos(angle) * pillarRadius
          const z = Math.sin(angle) * pillarRadius
          return (
            <mesh key={i} position={[x, 5, z]}>
              <cylinderGeometry args={[0.1, 0.1, 40, 16]} />
              <meshStandardMaterial 
                color="#ffffff" 
                emissive="#00e5ff" 
                emissiveIntensity={1.5} 
                transparent 
                opacity={0.8} 
              />
            </mesh>
          )
        })}
      </group>

      {/* Floating Info Blocks */}
      <Float speed={1.5} rotationIntensity={0.1} floatIntensity={0.5} position={[0, 5, 0]}>
        <Text fontSize={2.5} color="white" maxWidth={40} textAlign="center" position={[0, 4, 0]}>
          DEPARTMENT OF INFORMATION TECHNOLOGY
        </Text>
        
        <Text fontSize={1.2} color="#cccccc" position={[0, 1, 0]}>
          Pimpri Chinchwad College of Engineering
        </Text>
        
        <Text fontSize={0.8} color="#888888" position={[0, -1, 0]}>
          Established 2001 | B.Tech Intake: 180
        </Text>

        <group position={[0, -4, 0]}>
          <Text fontSize={0.6} color="#00e5ff" position={[-6, 0, 0]}>
            NBA Accredited
          </Text>
          <Text fontSize={0.6} color="#00e5ff" position={[0, 0, 0]}>
            NAAC 'A++' Grade
          </Text>
          <Text fontSize={0.6} color="#00e5ff" position={[6, 0, 0]}>
            Autonomous Status
          </Text>
        </group>
      </Float>

      {/* Floating PCCOE Badge */}
      <Float speed={2} rotationIntensity={0.8} floatIntensity={1} position={[0, 15, 0]}>
        <mesh>
          <torusGeometry args={[3, 0.1, 16, 100]} />
          <meshStandardMaterial color="#00e5ff" emissive="#00e5ff" emissiveIntensity={2} />
        </mesh>
        <Text fontSize={1.5} color="white" position={[0, 0, 0]}>
          PCCOE
        </Text>
      </Float>
    </group>
  )
}
