import { feature } from 'topojson-client';
import world from 'world-atlas/countries-110m.json';

/** ISO 3166 alpha 2 to the numeric id used in the world-atlas map. Same countries as COUNTRY_CENTRE in `geo.py`. */
const NUMERIC: Record<string, string> = {
  PL: '616', MX: '484', CN: '156', NL: '528', US: '840', SG: '702', DE: '276', FR: '250', GB: '826', ES: '724',
  IT: '380', BR: '076', IN: '356', JP: '392', AE: '784', ZA: '710', KE: '404', TR: '792', AU: '036', CA: '124',
};

export type Country = { id: string; name: string };
export type CountryShape = { id?: string | number; properties: { name?: string } };

/** Country outlines from Natural Earth through the world-atlas package (public domain, see design_system/assets/CREDITS.md). */
export function countryShapes(): CountryShape[] {
  const topology = world as unknown as Parameters<typeof feature>[0];
  const objects = (topology as unknown as { objects: Record<string, never> }).objects;
  const collection = feature(topology, objects.countries) as unknown as { features: CountryShape[] };
  return collection.features;
}

/** Map ids of the countries that hold a plant or a channel. */
export function activeCountryIds(countries: string[]): Set<string> {
  return new Set(countries.flatMap((c) => (NUMERIC[c] ? [NUMERIC[c]] : [])));
}
