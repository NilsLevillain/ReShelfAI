import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useSource } from '../data/DataSource';
import { useTheme } from '../theme';
import { Icon, IconSprite } from './Icon';
import { Stepper } from './Stepper';

type NavItem = { to: string; label: string; icon: string; step?: number };

export const NAV: NavItem[] = [
  { to: '/', label: 'Home', icon: 'flag' },
  { to: '/stock', label: 'Stock', icon: 'box' },
  { to: '/parameters', label: 'Parameters', icon: 'sliders', step: 0 },
  { to: '/results', label: 'Results', icon: 'chart', step: 2 },
  { to: '/compare', label: 'Compare', icon: 'scale', step: 2 },
];

export function Shell() {
  const [theme, toggle] = useTheme();
  const source = useSource();
  const { pathname } = useLocation();
  const step = NAV.find((n) => n.to === pathname)?.step;

  return (
    <>
      <IconSprite />
      <header className="rs-nav">
        <div className="rs-nav__in">
          <NavLink className="rs-brand" to="/" aria-label="Reshelf home">
            <span className="rs-wordmark">Reshelf</span>
          </NavLink>
          <nav className="rs-tabs" aria-label="Main">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === '/'} className="rs-tab">
                <Icon name={n.icon} />
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="rs-nav__right">
            <span className="rs-badge" data-testid="simulated-badge">
              Simulated data
            </span>
            <button
              className="rs-iconbtn"
              type="button"
              aria-label="Switch theme"
              title={`Theme: ${theme}`}
              onClick={toggle}
            >
              <Icon name="sun" className="rs-theme-sun" />
              <Icon name="moon" className="rs-theme-moon" />
            </button>
          </div>
        </div>
      </header>
      <div
        className={`rs-callout ${source === 'live' ? '' : 'rs-callout--info'}`}
        data-testid="data-source-banner"
        role="status"
      >
        {source === null ? 'Checking the data source' : source === 'live' ? 'Live solver' : 'Cached results'}
      </div>
      <main className="rs-page">
        {step !== undefined && <Stepper current={step} />}
        <Outlet />
      </main>
    </>
  );
}
