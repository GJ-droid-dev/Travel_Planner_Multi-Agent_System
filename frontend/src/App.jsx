import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import StatusPage from './pages/StatusPage';
import ItineraryPage from './pages/ItineraryPage';
import RetrievePage from './pages/RetrievePage';
import ErrorPage from './pages/ErrorPage';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/status/:planId" element={<StatusPage />} />
          <Route path="/itinerary/:planId" element={<ItineraryPage />} />
          <Route path="/retrieve" element={<RetrievePage />} />
          <Route path="/error" element={<ErrorPage />} />
          <Route path="*" element={<ErrorPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
