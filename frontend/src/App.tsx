import { Link, Route, Routes } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import SubmissionPage from './features/submission/SubmissionPage';
import ScanStatusPage from './features/scans/ScanStatusPage';
import ResultPage from './features/report/ResultPage';
import ReportPage from './features/report/ReportPage';
import HistoryPage from './features/scans/HistoryPage';

export default function App() {
  const { t, i18n } = useTranslation();
  const toggleLanguage = () => {
    const next = i18n.language === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(next);
    localStorage.setItem('cybersathi-lang', next);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🛡️</span>
            <div>
              <h1 className="font-extrabold text-brand-900 leading-tight">{t('app.title')}</h1>
              <p className="text-xs text-slate-500 hidden sm:block">{t('app.subtitle')}</p>
            </div>
          </Link>

          <div className="flex items-center gap-4">
            <Link to="/history" className="text-xs sm:text-sm font-semibold text-slate-600 hover:text-slate-900">
              {t('nav.history')}
            </Link>
            <button
              onClick={toggleLanguage}
              className="border border-slate-300 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-50 hover:bg-slate-100 text-slate-700"
            >
              {i18n.language === 'en' ? 'हिन्दी' : 'English'}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<SubmissionPage />} />
          <Route path="/scan/:scanId" element={<ScanStatusPage />} />
          <Route path="/scan/:scanId/result" element={<ResultPage />} />
          <Route path="/scan/:scanId/report" element={<ReportPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        National Cybercrime Helpline: <b>1930</b> | File complaints officially at{' '}
        <a href="https://cybercrime.gov.in" target="_blank" rel="noreferrer" className="underline font-semibold">
          cybercrime.gov.in
        </a>
      </footer>
    </div>
  );
}