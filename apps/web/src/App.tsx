import { Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { Placeholder } from './pages/Placeholder';
import { Compare } from './pages/Compare';
import { Results } from './pages/Results';
import { Stock } from './pages/Stock';

export function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route
          index
          element={<Placeholder title="Tighten a rule. See what it costs. See why." lede="Give sleeping stock a second shelf." />}
        />
        <Route path="stock" element={<Stock />} />
        <Route path="parameters" element={<Placeholder title="Parameters" lede="Rule dials arrive in week 5." />} />
        <Route path="results" element={<Results />} />
        <Route path="compare" element={<Compare />} />
        <Route path="*" element={<Placeholder title="Page not found" lede="Use the menu above." />} />
      </Route>
    </Routes>
  );
}
