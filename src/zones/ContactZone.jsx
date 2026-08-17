import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useWorldStore } from '../store/worldStore';

export function ContactZone() {
  const portalRef = useRef();
  const shaderRef = useRef();
  const particlesRef = useRef();
  const setHoveredObject = useWorldStore((state) => state.setHoveredObject);

  const vertexShader = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    uniform float time;
    varying vec2 vUv;
    
    // Simplex 2D noise
    vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
    float snoise(vec2 v){
      const vec4 C = vec4(0.211324865405187, 0.366025403784439,
               -0.577350269189626, 0.024390243902439);
      vec2 i  = floor(v + dot(v, C.yy) );
      vec2 x0 = v -   i + dot(i, C.xx);
      vec2 i1;
      i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
      vec4 x12 = x0.xyxy + C.xxzz;
      x12.xy -= i1;
      i = mod(i, 289.0);
      vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
      + i.x + vec3(0.0, i1.x, 1.0 ));
      vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
        dot(x12.zw,x12.zw)), 0.0);
      m = m*m ;
      m = m*m ;
      vec3 x = 2.0 * fract(p * C.www) - 1.0;
      vec3 h = abs(x) - 0.5;
      vec3 ox = floor(x + 0.5);
      vec3 a0 = x - ox;
      m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
      vec3 g;
      g.x  = a0.x  * x0.x  + h.x  * x0.y;
      g.yz = a0.yz * x12.xz + h.yz * x12.yw;
      return 130.0 * dot(m, g);
    }

    void main() {
      vec2 p = vUv * 2.0 - 1.0;
      float r = length(p);
      float a = atan(p.y, p.x);
      
      // Spiral effect
      float spiral = a + r * 5.0 - time * 2.0;
      float noise = snoise(vec2(cos(spiral), sin(spiral)) * 2.0 + time);
      
      // Mask circle
      float mask = smoothstep(1.0, 0.8, r);
      
      // Colors
      vec3 col1 = vec3(1.0, 0.25, 0.5); // Magenta
      vec3 col2 = vec3(0.0, 1.0, 1.0); // Cyan
      vec3 col3 = vec3(0.3, 0.0, 0.5); // Dark Purple
      
      vec3 finalCol = mix(col3, col1, noise + r);
      finalCol = mix(finalCol, col2, sin(spiral * 2.0) * 0.5 + 0.5);
      
      gl_FragColor = vec4(finalCol, mask * (0.5 + noise * 0.5));
    }
  `;

  const uniforms = useMemo(() => ({
    time: { value: 0 }
  }), []);

  // Converging particles
  const particleCount = 200;
  const particlePositions = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 20;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 20;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    return pos;
  }, [particleCount]);

  useFrame((state, delta) => {
    if (shaderRef.current) {
      shaderRef.current.uniforms.time.value = state.clock.getElapsedTime();
    }
    
    if (portalRef.current) {
      portalRef.current.rotation.z += delta * 0.5;
    }

    if (particlesRef.current) {
      const positions = particlesRef.current.geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        // Move towards center (0,0,0)
        positions[i * 3] *= 0.99;
        positions[i * 3 + 1] *= 0.99;
        positions[i * 3 + 2] *= 0.99;
        
        // Reset if too close
        if (Math.abs(positions[i * 3]) < 0.1 && Math.abs(positions[i * 3 + 1]) < 0.1) {
          positions[i * 3] = (Math.random() - 0.5) * 20;
          positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
          positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
        }
      }
      particlesRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  const contactInfo = [
    { text: 'Pccoeitdept@gmail.com', pos: [-6, 3, 2] },
    { text: '020-27600061-2222', pos: [6, 2, 1] },
    { text: 'PCCOE, Nigdi, Pune 411044', pos: [-5, -3, 3] },
    { text: 'it.pccoepune.com', pos: [5, -2, 2] },
  ];

  return (
    <group position={[0, 0, -95]}>
      {/* Central Portal */}
      <group ref={portalRef}>
        <mesh>
          <torusGeometry args={[4, 0.2, 16, 100]} />
          <meshStandardMaterial color="#ff4081" emissive="#ff4081" emissiveIntensity={2} />
        </mesh>
        
        {/* Inside Portal Vortex */}
        <mesh>
          <planeGeometry args={[7.8, 7.8]} />
          <shaderMaterial
            ref={shaderRef}
            vertexShader={vertexShader}
            fragmentShader={fragmentShader}
            uniforms={uniforms}
            transparent
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>

      {/* Contact Info Text */}
      {contactInfo.map((info, i) => (
        <Text
          key={i}
          position={info.pos}
          fontSize={0.8}
          color="#ffffff"
          outlineWidth={0.05}
          outlineColor="#ff4081"
          onPointerOver={() => setHoveredObject(`contact-${i}`)}
          onPointerOut={() => setHoveredObject(null)}
        >
          {info.text}
        </Text>
      ))}

      {/* Converging Particles */}
      <Points ref={particlesRef} positions={particlePositions}>
        <PointMaterial transparent color="#00e5ff" size={0.1} sizeAttenuation depthWrite={false} />
      </Points>

      {/* Portal Light */}
      <pointLight position={[0, 0, 2]} intensity={100} color="#ff4081" distance={20} />
      <ambientLight intensity={0.2} />
    </group>
  );
}
