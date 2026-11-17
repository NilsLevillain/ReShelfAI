import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import Globe, { type GlobeMethods } from 'react-globe.gl';
import { activeCountryIds, countryShapes, type CountryShape } from './countries';
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

/** The theme set on the page root. The globe reads colors once per theme, so it needs to know when this changes. */
function useRootTheme(): string {
  const root = document.documentElement;
  const [theme, setTheme] = useState(root.getAttribute('data-theme') ?? 'light');
  useEffect(() => {
    const watcher = new MutationObserver(() => setTheme(root.getAttribute('data-theme') ?? 'light'));
    watcher.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    return () => watcher.disconnect();
  }, [root]);
  return theme;
}

/** The WebGL part, in its own chunk. Colors come from the design system variables. */
export default function GlobeCanvas({
  geo,
  selected,
  onSelect,
  labelOf,
}: {
  geo: Geo;
  selected?: string;
  onSelect: (plant: string) => void;
  /** HTML of the hover card for a plant, a channel or a country (map id). */
  labelOf: (kind: 'plant' | 'channel' | 'country', code: string) => string;
}) {
  const theme = useRootTheme();
  const globe = useRef<GlobeMethods | undefined>(undefined);
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(560);
  useLayoutEffect(() => {
    const el = box.current;
    if (!el) return;
    const fit = () => setWidth(Math.max(320, Math.min(900, el.clientWidth || 560)));
    fit();
    const watcher = new ResizeObserver(fit);
    watcher.observe(el);
    return () => watcher.disconnect();
  }, []);

  // The sea is a one pixel texture in a design system color. Countries are drawn as polygons on top.
  const colors = useMemo(() => {
    void theme;
    return {
      sea: css('--rs-bg-info') ?? '#e6f1ff',
      land: css('--rs-bg-surface') ?? '#ffffff',
      active: css('--rs-bg-hint') ?? '#ddefe4',
      outline: css('--rs-border-strong') ?? '#898989',
      activeOutline: css('--rs-border-brand') ?? '#187573',
      plant: css('--rs-compare-delta-cost'),
      channel: css('--rs-compare-optimizer'),
    };
  }, [theme]);
  const surface = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = colors.sea;
      ctx.fillRect(0, 0, 1, 1);
    }
    return canvas.toDataURL();
  }, [colors.sea]);

  const shapes = useMemo(() => countryShapes(), []);
  const active = useMemo(
    () => activeCountryIds([...geo.plants.map((p) => p.country), ...geo.channels.map((c) => c.country)]),
    [geo],
  );
  const isActive = (d: object) => active.has(String((d as CountryShape).id ?? ''));

  const byCode = new Map([...geo.plants, ...geo.channels].map((p) => [('plant' in p ? p.plant : p.channel), p]));
  const maxRisk = Math.max(1, ...geo.plants.map((p) => p.value_at_risk));
  const points = [
    ...geo.plants.map((p) => ({ lat: p.lat, lng: p.lon, size: 0.02 + (0.1 * p.value_at_risk) / maxRisk, color: colors.plant, plant: p.plant, kind: 'plant' as const, code: p.plant })),
    ...geo.channels.map((c) => ({ lat: c.lat, lng: c.lon, size: 0.01, color: colors.channel, plant: '', kind: 'channel' as const, code: c.channel })),
  ];
  const arcs = geo.arcs.flatMap((a) => {
    const p = byCode.get(a.plant);
    const c = byCode.get(a.channel);
    return p && c ? [{ startLat: p.lat, startLng: p.lon, endLat: c.lat, endLng: c.lon, units: a.units }] : [];
  });
  const maxUnits = Math.max(1, ...geo.arcs.map((a) => a.units));

  // Open on the stock: the view starts at the value weighted centre of the plants, not on an empty ocean.
  const lookAtPlants = () => {
    const total = geo.plants.reduce((s, p) => s + p.value_at_risk, 0);
    if (!total) return;
    const lat = geo.plants.reduce((s, p) => s + p.lat * p.value_at_risk, 0) / total;
    const lng = geo.plants.reduce((s, p) => s + p.lon * p.value_at_risk, 0) / total;
    globe.current?.pointOfView({ lat, lng, altitude: 1.8 }, 0);
  };

  return (
    <div ref={box} className="rs-globe__box">
    <Globe
      ref={globe}
      onGlobeReady={lookAtPlants}
      polygonsData={shapes}
      polygonCapColor={(d) => (isActive(d as object) ? colors.active : colors.land)}
      polygonSideColor={() => 'rgba(0,0,0,0)'}
      polygonStrokeColor={(d) => (isActive(d as object) ? colors.activeOutline : colors.outline)}
      polygonAltitude={(d) => (isActive(d as object) ? 0.012 : 0.006)}
      polygonLabel={(d) => labelOf('country', String((d as CountryShape).id ?? '')) || (d as CountryShape).properties.name || ''}
      width={width}
      height={Math.round(width * 0.6)}
      backgroundColor="rgba(0,0,0,0)"
      globeImageUrl={surface}
      showAtmosphere={false}
      pointsData={points}
      pointLat="lat"
      pointLng="lng"
      pointAltitude="size"
      pointRadius={(d) => ((d as { plant: string }).plant === selected ? 0.9 : 0.5)}
      pointColor="color"
      pointLabel={(d) => labelOf((d as { kind: 'plant' | 'channel' }).kind, (d as { code: string }).code)}
      onPointClick={(d) => {
        const code = (d as { plant: string }).plant;
        if (code) onSelect(code);
      }}
      arcsData={arcs}
      arcColor={() => colors.channel ?? '#0f766e'}
      arcStroke={(d) => 0.2 + (0.8 * (d as { units: number }).units) / maxUnits}
      arcDashLength={1}
      arcDashGap={0}
      arcDashAnimateTime={0}
    />
    </div>
  );
}
