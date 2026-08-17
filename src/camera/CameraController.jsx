import { useEffect, useRef } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import { useWorldStore, CAMERA_TARGETS } from '../store/worldStore';
import gsap from 'gsap';
import * as THREE from 'three';

export default function CameraController() {
  const { camera } = useThree();
  const currentZone = useWorldStore((state) => state.currentZone);
  const isTransitioning = useWorldStore((state) => state.isTransitioning);
  const setTransitioning = useWorldStore((state) => state.setTransitioning);
  
  // Ref for the camera's lookAt target
  const lookAtTarget = useRef(new THREE.Vector3(0, 0, 0));
  
  // Refs for mouse position
  const mouse = useRef({ x: 0, y: 0 });
  const targetMouse = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event) => {
      // Normalize to -1 to +1
      mouse.current.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.current.y = -(event.clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    if (!CAMERA_TARGETS || !CAMERA_TARGETS[currentZone]) return;

    const target = CAMERA_TARGETS[currentZone];
    
    setTransitioning(true);

    // Animate camera position
    gsap.to(camera.position, {
      x: target.position[0],
      y: target.position[1],
      z: target.position[2],
      duration: 2.5,
      ease: 'power3.inOut',
    });

    // Animate lookAt target
    gsap.to(lookAtTarget.current, {
      x: target.lookAt[0],
      y: target.lookAt[1],
      z: target.lookAt[2],
      duration: 2.5,
      ease: 'power3.inOut',
      onUpdate: () => {
        camera.lookAt(lookAtTarget.current);
      },
      onComplete: () => {
        setTransitioning(false);
      }
    });

  }, [currentZone, camera, setTransitioning]);

  useFrame((state, delta) => {
    // Smoothly interpolate mouse target for weight/damping
    targetMouse.current.x = THREE.MathUtils.lerp(targetMouse.current.x, mouse.current.x, 2 * delta);
    targetMouse.current.y = THREE.MathUtils.lerp(targetMouse.current.y, mouse.current.y, 2 * delta);

    if (!isTransitioning) {
      // Apply parallax offset based on current zone's base position
      const baseTarget = CAMERA_TARGETS && CAMERA_TARGETS[currentZone] ? CAMERA_TARGETS[currentZone].position : camera.position;
      
      const parallaxX = targetMouse.current.x * 0.5;
      const parallaxY = targetMouse.current.y * 0.5;

      camera.position.x = THREE.MathUtils.lerp(camera.position.x, baseTarget[0] + parallaxX, 2 * delta);
      camera.position.y = THREE.MathUtils.lerp(camera.position.y, baseTarget[1] + parallaxY, 2 * delta);
      
      // Keep looking at target with the parallax offset applied
      camera.lookAt(lookAtTarget.current);
    }
  });

  return null;
}
