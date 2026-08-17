// Fresnel edge glow shader
export const fresnelVertexShader = `
  varying vec3 vWorldNormal;
  varying vec3 vViewDirection;
  varying vec2 vUv;
  
  void main() {
    vUv = uv;
    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
    vWorldNormal = normalize(normalMatrix * normal);
    vViewDirection = normalize(cameraPosition - worldPosition.xyz);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const fresnelFragmentShader = `
  uniform vec3 uColor;
  uniform float uIntensity;
  uniform float uPower;
  uniform float uTime;
  
  varying vec3 vWorldNormal;
  varying vec3 vViewDirection;
  varying vec2 vUv;
  
  void main() {
    float fresnel = pow(1.0 - abs(dot(vWorldNormal, vViewDirection)), uPower);
    float pulse = 0.8 + 0.2 * sin(uTime * 1.5);
    vec3 color = uColor * fresnel * uIntensity * pulse;
    float alpha = fresnel * 0.8;
    gl_FragColor = vec4(color, alpha);
  }
`;

// Grid shader
export const gridVertexShader = `
  varying vec2 vUv;
  varying vec3 vWorldPos;
  
  void main() {
    vUv = uv;
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vWorldPos = worldPos.xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const gridFragmentShader = `
  uniform float uTime;
  uniform vec3 uColor;
  uniform float uOpacity;
  
  varying vec2 vUv;
  varying vec3 vWorldPos;
  
  void main() {
    vec2 grid = abs(fract(vWorldPos.xz * 0.1) - 0.5);
    float line = min(grid.x, grid.y);
    float gridLine = 1.0 - smoothstep(0.0, 0.03, line);
    
    vec2 grid2 = abs(fract(vWorldPos.xz * 0.02) - 0.5);
    float line2 = min(grid2.x, grid2.y);
    float majorLine = 1.0 - smoothstep(0.0, 0.02, line2);
    
    float dist = length(vWorldPos.xz) * 0.01;
    float falloff = exp(-dist * 0.5);
    
    float pulse = sin(length(vWorldPos.xz) * 0.05 - uTime * 2.0) * 0.5 + 0.5;
    
    float combined = (gridLine * 0.3 + majorLine * 0.7) * falloff;
    combined += majorLine * pulse * 0.2 * falloff;
    
    vec3 color = uColor * combined;
    float alpha = combined * uOpacity;
    
    gl_FragColor = vec4(color, alpha);
  }
`;

// Portal shader
export const portalVertexShader = `
  varying vec2 vUv;
  
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const portalFragmentShader = `
  uniform float uTime;
  uniform vec3 uColor1;
  uniform vec3 uColor2;
  
  varying vec2 vUv;
  
  // Simple noise
  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }
  
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }
  
  void main() {
    vec2 center = vUv - 0.5;
    float dist = length(center);
    float angle = atan(center.y, center.x);
    
    float spiral = sin(angle * 5.0 - uTime * 3.0 + dist * 10.0) * 0.5 + 0.5;
    float n = noise(vec2(angle * 2.0, dist * 5.0 - uTime));
    
    float ring = smoothstep(0.45, 0.3, dist) * smoothstep(0.0, 0.1, dist);
    
    vec3 color = mix(uColor1, uColor2, spiral * n);
    color *= ring;
    color += uColor1 * 0.1 * ring;
    
    float alpha = ring * (0.6 + 0.4 * spiral);
    
    gl_FragColor = vec4(color, alpha);
  }
`;

// Particle shader
export const particleVertexShader = `
  attribute float aScale;
  attribute float aRandom;
  
  uniform float uTime;
  uniform float uSize;
  
  varying float vAlpha;
  
  void main() {
    vec3 pos = position;
    pos.y += sin(uTime * 0.3 + aRandom * 6.28) * 0.5;
    pos.x += cos(uTime * 0.2 + aRandom * 3.14) * 0.3;
    
    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_PointSize = uSize * aScale * (200.0 / -mvPosition.z);
    gl_Position = projectionMatrix * mvPosition;
    
    vAlpha = smoothstep(200.0, 50.0, -mvPosition.z) * 0.6;
  }
`;

export const particleFragmentShader = `
  uniform vec3 uColor;
  
  varying float vAlpha;
  
  void main() {
    float dist = length(gl_PointCoord - 0.5);
    if (dist > 0.5) discard;
    
    float strength = 1.0 - (dist * 2.0);
    strength = pow(strength, 3.0);
    
    gl_FragColor = vec4(uColor, strength * vAlpha);
  }
`;

// Network flow shader
export const networkVertexShader = `
  varying vec2 vUv;
  
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const networkFragmentShader = `
  uniform float uTime;
  uniform vec3 uColor;
  
  varying vec2 vUv;
  
  void main() {
    float flow = fract(vUv.x * 3.0 - uTime * 0.5);
    flow = smoothstep(0.0, 0.3, flow) * smoothstep(1.0, 0.7, flow);
    
    vec3 color = uColor * flow;
    float alpha = flow * 0.8;
    
    gl_FragColor = vec4(color, alpha);
  }
`;
