import React from 'react';
import { useWorldStore, ZONES, ZONE_COLORS } from '../store/worldStore';

export default function HtmlOverlay() {
  const currentZone = useWorldStore((s) => s.currentZone);
  const navigateTo = useWorldStore((s) => s.navigateTo);
  const isTransitioning = useWorldStore((s) => s.isTransitioning);

  const zoneName = {
    NEXUS: 'ITSA DIGITAL NEXUS',
    EVENTS: 'EVENT ARENA',
    PROJECTS: 'BUILD FIELD',
    COMMUNITY: 'NETWORK CITY',
    COMPETE: 'CHALLENGE ARENA',
    LEARN: 'KNOWLEDGE ARCHIVE',
    ABOUT: 'ABOUT ITSA',
    CONTACT: 'CONTACT PORTAL',
    PEOPLE: 'PEOPLE OF ITSA',
  }[currentZone] || 'NEXUS';

  return (
    <>
      {/* Zone indicator */}
      <div
        className="zone-indicator"
        style={{
          borderColor: `${ZONE_COLORS[currentZone]}33`,
          transition: 'all 0.8s ease',
        }}
      >
        {zoneName}
      </div>

      {/* Back button */}
      <button
        className={`back-button ${currentZone !== ZONES.NEXUS ? 'visible' : ''}`}
        onClick={() => navigateTo(ZONES.NEXUS)}
        disabled={isTransitioning}
        aria-label="Return to Nexus"
      >
        ← NEXUS
      </button>

      {/* Navigation hint */}
      {currentZone === ZONES.NEXUS && (
        <div className="nav-hint">
          CLICK ON FLOATING OBJECTS TO EXPLORE
        </div>
      )}

      {/* Semantic HTML for SEO / Accessibility */}
      <div className="sr-only" role="main" aria-label="ITSA Digital Nexus">
        <h1>ITSA — Information Technology Students Association, PCCOE</h1>
        <nav aria-label="Main Navigation">
          <ul>
            {Object.values(ZONES).filter(z => z !== 'NEXUS').map(zone => (
              <li key={zone}>
                <button onClick={() => navigateTo(zone)}>
                  {zone}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        <section aria-label="About">
          <h2>Department of Information Technology</h2>
          <p>Pimpri Chinchwad College of Engineering (PCCOE), Pune</p>
          <p>NBA Accredited | NAAC 'A' Grade | Autonomous | AICTE Approved | Affiliated to SPPU</p>
        </section>
        <section aria-label="Contact">
          <p>Email: Pccoeitdept@gmail.com</p>
          <p>Phone: 020-27600061-2222</p>
          <p>Address: Near Akurdi Railway Station Road, Sector No. 26, Pradhikaran, Nigdi, Pimpri, Maharashtra 411044</p>
        </section>
      </div>
    </>
  );
}
