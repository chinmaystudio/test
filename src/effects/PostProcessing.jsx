import React from 'react';
import { EffectComposer, Bloom, Vignette, ChromaticAberration } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import { useWorldStore } from '../store/worldStore';

export default function PostProcessing() {
  const performanceTier = useWorldStore((s) => s.performanceTier);

  if (performanceTier === 'LOW') return null;

  const isHigh = performanceTier === 'HIGH';

  return (
    <EffectComposer multisampling={isHigh ? 4 : 0}>
      <Bloom
        intensity={1.2}
        luminanceThreshold={0.2}
        luminanceSmoothing={0.9}
        mipmapBlur
        radius={0.8}
      />
      <Vignette
        offset={0.3}
        darkness={0.6}
        blendFunction={BlendFunction.NORMAL}
      />
      {isHigh && (
        <ChromaticAberration
          blendFunction={BlendFunction.NORMAL}
          offset={[0.0005, 0.0005]}
          radialModulation={true}
          modulationOffset={0.5}
        />
      )}
    </EffectComposer>
  );
}
