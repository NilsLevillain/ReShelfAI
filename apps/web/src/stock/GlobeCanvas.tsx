import { useMemo } from 'react';
import Globe from 'react-globe.gl';
import type { Geo } from './GlobePanel';

/** A design system variable as a plain rgb string. A probe element resolves var() chains that three.js cannot parse. */
const css = (name: string) => {
  const probe = document.createElement('span');
  probe.style.color = `var(${name})`;
  document.body.appendChild(probe);
  const value = getComputedStyle(probe).color;
  probe.remove();
  return value || undefined;
};

/** The WebGL part, in its own chunk. Colors come from the design system variables. */
export default function GlobeCanvas({
  geo,
  selected,
  onSelect,
}: {
  geo: Geo;
  selected?: string;
  onSelect: (plant: string) => void;
}) {
  // The globe has no map, so its surface is a one pixel texture in a design system color.
  const surface = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = css('--rs-border-default') ?? '#dadada';
      ctx.fillRect(0, 0, 1, 1);
    }
    return canvas.toDataURL();
  }, []);
  const plantColor = css('--rs-compare-delta-cost');
  const channelColor = css('--rs-compare-optimizer');
  const byCode = new Map([...geo.plants, ...geo.channels].map((p) => [('plant' in p ? p.plant : p.channel), p]));
  const maxRisk = Math.max(1, ...geo.plants.map((p) => p.value_at_risk));
  const points = [
    ...geo.plants.map((p) => ({ lat: p.lat, lng: p.lon, size: 0.02 + (0.1 * p.value_at_risk) / maxRisk, color: plantColor, plant: p.plant })),
    ...geo.channels.map((c) => ({ lat: c.lat, lng: c.lon, size: 0.01, color: channelColor, plant: '' })),
  ];
  const arcs = geo.arcs.flatMap((a) => {
    const p = byCode.get(a.plant);
    const c = byCode.get(a.channel);
    return p && c ? [{ startLat: p.lat, startLng: p.lon, endLat: c.lat, endLng: c.lon, units: a.units }] : [];
  });
  const maxUnits = Math.max(1, ...geo.arcs.map((a) => a.units));

  return (
    <Globe
      showGraticules
      width={560}
      height={420}
      backgroundColor="rgba(0,0,0,0)"
      globeImageUrl={surface}
      showAtmosphere={false}
      pointsData={points}
      pointLat="lat"
      pointLng="lng"
      pointAltitude="size"
      pointRadius={(d) => ((d as { plant: string }).plant === selected ? 0.9 : 0.5)}
      atmosphereColor={plantColor}
      pointColor="color"
      onPointClick={(d) => {
        const code = (d as { plant: string }).plant;
        if (code) onSelect(code);
      }}
      arcsData={arcs}
      arcColor={() => channelColor ?? '#0f766e'}
      arcStroke={(d) => 0.2 + (0.8 * (d as { units: number }).units) / maxUnits}
      arcDashLength={1}
      arcDashGap={0}
      arcDashAnimateTime={0}
    />
  );
}
