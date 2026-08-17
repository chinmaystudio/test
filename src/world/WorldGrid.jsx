import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWorldStore, ZONE_COLORS } from '../store/worldStore';

const vertexShader = `
  varying vec2 vUv;
  varying vec3 vWorldPosition;
  void main() {
    vUv = uv;
    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
    vWorldPosition = worldPosition.xyz;
    gl_Position = projectionMatrix * viewMatrix * worldPosition;
  }
`;

const fragmentShader = `
  varying vec2 vUv;
  varying vec3 vWorldPosition;
  uniform float time;
  uniform vec3 color;

  void main() {
    vec2 grid = abs(fract(vWorldPosition.xz / 4.0 - 0.5) - 0.5) / fwidth(vWorldPosition.xz / 4.0);
    float line = min(grid.x, grid.y);
    
    float distance = length(vWorldPosition.xz);
    float pulse = sin(distance * 0.2 - time * 2.0) * 0.5 + 0.5;
    
    float alpha = 1.0 - min(line, 1.0);
    alpha *= smoothstep(100.0, 0.0, distance); // Fade out at edges
    alpha *= pulse * 0.8 + 0.2; // Add pulsing effect
    
    gl_FragColor = vec4(color, alpha * 0.5);
  }
`;

export default function WorldGrid() {
  const materialRef = useRef();
  const currentZone = useWorldStore((state) => state.currentZone);
  const targetColor = useMemo(() => new THREE.Color(), []);

  useFrame((state, delta) => {
    if (materialRef.current) {
      materialRef.current.uniforms.time.value = state.clock.getElapsedTime();
      
      const zoneColor = ZONE_COLORS && ZONE_COLORS[currentZone] ? ZONE_COLORS[currentZone] : '#00d4ff';
      targetColor.set(zoneColor);
      materialRef.current.uniforms.color.value.lerp(targetColor, delta * 2);
    }
  });

  const uniforms = useMemo(() => ({
    time: { value: 0 },
    color: { value: new THREE.Color('#00d4ff') }
  }), []);

  return (
    <mesh position={[0, -2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[200, 200]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}
