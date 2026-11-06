import { Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { Placeholder } from './pages/Placeholder';
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
        <Route path="results" element={<Placeholder title="Results" lede="Results arrive in slice 3." />} />
        <Route path="compare" element={<Placeholder title="Compare" lede="Compare arrives in slice 3." />} />
        <Route path="*" element={<Placeholder title="Page not found" lede="Use the menu above." />} />
      </Route>
    </Routes>
  );
}
