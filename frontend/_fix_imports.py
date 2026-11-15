# Clean main.tsx
main = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
"""
with open('src/main.tsx', 'w', encoding='utf-8') as f:
    f.write(main)

# Clean App.tsx
app = """import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ReportPage from './pages/ReportPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ReportPage />} />
      </Routes>
    </BrowserRouter>
  );
}
"""
with open('src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(app)

print('✅ main.tsx and App.tsx rewritten (no App.css import)')