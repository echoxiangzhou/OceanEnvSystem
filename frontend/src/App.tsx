import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import { ToastProvider } from './hooks/use-toast';
import Dashboard from './pages/Dashboard';
import TestComponents from './pages/TestComponents';

function App() {
  return (
    <ToastProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Test Route */}
            <Route path="/test" element={<TestComponents />} />
            {/* Add more routes as needed */}
          </Routes>
        </Layout>
      </Router>
    </ToastProvider>
  );
}

export default App;