import { create } from 'zustand';

export const ZONES = {
  NEXUS: 'NEXUS',
  EVENTS: 'EVENTS',
  PROJECTS: 'PROJECTS',
  COMMUNITY: 'COMMUNITY',
  COMPETE: 'COMPETE',
  LEARN: 'LEARN',
  ABOUT: 'ABOUT',
  CONTACT: 'CONTACT',
  PEOPLE: 'PEOPLE',
};

export const ZONE_COLORS = {
  NEXUS: '#00d4ff',
  EVENTS: '#00e5ff',
  PROJECTS: '#aa00ff',
  COMMUNITY: '#00e676',
  COMPETE: '#ff6d00',
  LEARN: '#ffd600',
  ABOUT: '#e0e0e0',
  CONTACT: '#ff4081',
  PEOPLE: '#7c4dff',
};

export const CAMERA_TARGETS = {
  NEXUS: { position: [0, 3, 18], lookAt: [0, 0, 0] },
  EVENTS: { position: [45, 6, 5], lookAt: [45, 2, -10] },
  PROJECTS: { position: [-45, 8, -15], lookAt: [-45, 4, -30] },
  COMMUNITY: { position: [5, 5, -55], lookAt: [0, 2, -65] },
  COMPETE: { position: [35, 10, -45], lookAt: [35, 5, -60] },
  LEARN: { position: [-35, 18, 35], lookAt: [-35, 10, 20] },
  ABOUT: { position: [0, 12, 55], lookAt: [0, 8, 45] },
  CONTACT: { position: [0, 3, -85], lookAt: [0, 2, -95] },
  PEOPLE: { position: [55, 8, 25], lookAt: [55, 4, 15] },
};

export const useWorldStore = create((set, get) => ({
  currentZone: ZONES.NEXUS,
  previousZone: null,
  setZone: (zone) => set({ previousZone: get().currentZone, currentZone: zone }),

  cameraTarget: CAMERA_TARGETS.NEXUS,
  setCameraTarget: (target) => set({ cameraTarget: target }),

  isLoading: true,
  loadingProgress: 0,
  setLoading: (isLoading) => set({ isLoading }),
  setLoadingProgress: (loadingProgress) => set({ loadingProgress }),

  performanceTier: 'HIGH',
  setPerformanceTier: (performanceTier) => set({ performanceTier }),

  hoveredObject: null,
  setHoveredObject: (hoveredObject) => set({ hoveredObject }),

  isTransitioning: false,
  setTransitioning: (isTransitioning) => set({ isTransitioning }),

  navigateTo: (zone) => {
    const state = get();
    if (state.currentZone === zone || state.isTransitioning) return;
    set({
      isTransitioning: true,
      previousZone: state.currentZone,
      currentZone: zone,
      cameraTarget: CAMERA_TARGETS[zone],
    });
    setTimeout(() => set({ isTransitioning: false }), 2500);
  },
}));
