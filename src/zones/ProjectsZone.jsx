import React, { useState } from 'react'
import { Text, Float, Line } from '@react-three/drei'
import * as THREE from 'three'
import { useWorldStore } from '../store/worldStore'
import projects from '../data/projects'

function ProjectNode({ project, position }) {
  const [hovered, setHovered] = useState(false)
  const setHoveredObject = useWorldStore((state) => state.setHoveredObject)

  const scale = hovered ? 1.5 : 1
  const color = project.color || '#00e5ff'
  const emissiveIntensity = hovered ? 2 : 0.8

  const handlePointerOver = (e) => {
    e.stopPropagation()
    setHovered(true)
    setHoveredObject(project.id)
  }

  const handlePointerOut = (e) => {
    e.stopPropagation()
    setHovered(false)
    setHoveredObject(null)
  }

  const renderGeometry = () => {
    const type = project.type || 'box'
    switch(type.toLowerCase()) {
      case 'neural':
        return (
          <mesh>
            <icosahedronGeometry args={[1, 0]} />
            <meshStandardMaterial color={color} wireframe emissive={color} emissiveIntensity={emissiveIntensity} />
          </mesh>
        )
      case 'shield':
        return (
          <mesh>
            <octahedronGeometry args={[1, 0]} />
            <meshStandardMaterial color={color} wireframe emissive={color} emissiveIntensity={emissiveIntensity} />
          </mesh>
        )
      case 'network':
        return (
          <group>
            <mesh position={[0.6, 0.6, 0.6]}><sphereGeometry args={[0.2]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} /></mesh>
            <mesh position={[-0.6, -0.6, -0.6]}><sphereGeometry args={[0.2]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} /></mesh>
            <mesh position={[0.6, -0.6, 0.6]}><sphereGeometry args={[0.2]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} /></mesh>
            <mesh position={[-0.6, 0.6, -0.6]}><sphereGeometry args={[0.2]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} /></mesh>
            <Line points={[[0.6, 0.6, 0.6], [-0.6, -0.6, -0.6]]} color={color} opacity={0.5} transparent />
            <Line points={[[-0.6, -0.6, -0.6], [0.6, -0.6, 0.6]]} color={color} opacity={0.5} transparent />
            <Line points={[[-0.6, 0.6, -0.6], [0.6, -0.6, 0.6]]} color={color} opacity={0.5} transparent />
          </group>
        )
      case 'browser':
        return (
          <group>
            <mesh>
              <boxGeometry args={[1.5, 1, 0.2]} />
              <meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity * 0.5} />
            </mesh>
            <mesh position={[0, 0, 0.11]}>
              <planeGeometry args={[1.4, 0.9]} />
              <meshBasicMaterial color="#111111" />
            </mesh>
          </group>
        )
      case 'data':
        return (
          <mesh>
            <torusKnotGeometry args={[0.6, 0.15, 64, 8]} />
            <meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity} />
          </mesh>
        )
      case 'chain':
        return (
          <group>
            <mesh position={[-0.5, 0, 0]}><torusGeometry args={[0.4, 0.1, 16, 32]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity}/></mesh>
            <mesh position={[0, 0, 0]} rotation={[Math.PI/2, 0, 0]}><torusGeometry args={[0.4, 0.1, 16, 32]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity}/></mesh>
            <mesh position={[0.5, 0, 0]}><torusGeometry args={[0.4, 0.1, 16, 32]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={emissiveIntensity}/></mesh>
          </group>
        )
      default:
        return (
          <mesh>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color={color} wireframe emissive={color} emissiveIntensity={emissiveIntensity} />
          </mesh>
        )
    }
  }

  return (
    <Float position={position} speed={2} rotationIntensity={1} floatIntensity={2}>
      <group 
        scale={[scale, scale, scale]} 
        onPointerOver={handlePointerOver} 
        onPointerOut={handlePointerOut}
        onClick={() => console.log('Clicked project:', project.name)}
      >
        {renderGeometry()}
        <Text position={[0, -1.5, 0]} fontSize={0.4} color="white" anchorY="top">
          {project.name}
        </Text>
      </group>
    </Float>
  )
}

export default function ProjectsZone() {
  const projectPositions = [
    [-8, 3, -8], [8, 4, -5], [-4, 2, 6],
    [5, 5, 8], [-12, 3, 0], [12, 2, 4],
    [0, 6, -4], [-6, 4, 10], [6, 3, -12]
  ]

  return (
    <group position={[-45, 0, -30]}>
      {projects && projects.map((proj, i) => (
        <ProjectNode 
          key={`proj-${i}`} 
          project={proj} 
          position={projectPositions[i % projectPositions.length]} 
        />
      ))}
    </group>
  )
}
