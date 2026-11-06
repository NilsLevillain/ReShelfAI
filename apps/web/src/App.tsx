import { Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { RunProvider } from './data/run';
import { Compare } from './pages/Compare';
import { Home } from './pages/Home';
import { Parameters } from './pages/Parameters';
import { Placeholder } from './pages/Placeholder';
import { Results } from './pages/Results';
import { Stock } from './pages/Stock';

export function App() {
  return (
    <RunProvider>
      <Routes>
        <Route element={<Shell />}>
          <Route index element={<Home />} />
          <Route path="stock" element={<Stock />} />
          <Route path="parameters" element={<Parameters />} />
          <Route path="results" element={<Results />} />
          <Route path="compare" element={<Compare />} />
          <Route path="*" element={<Placeholder title="Page not found" lede="Use the menu above." />} />
        </Route>
      </Routes>
    </RunProvider>
  );
}
