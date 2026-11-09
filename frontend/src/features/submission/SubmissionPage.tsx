import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { createScan } from '../../shared/api';
import { saveHistory } from '../../shared/history';
import HelplineBanner from '../../shared/HelplineBanner';

export default function SubmissionPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [content, setContent] = useState('');
  const [lostMoney, setLostMoney] = useState(false);
  const [ack, setAck] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !ack) {
      setError('Please provide message text and accept the privacy notice.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const scan = await createScan(content, lostMoney);
      saveHistory({
        scan_id: scan.scan_id,
        status: scan.status,
        classification: scan.classification,
        date: new Date().toISOString(),
      });
      navigate(`/scan/${scan.scan_id}`);
    } catch {
      setError('Unable to analyze message. Please check the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {lostMoney && <HelplineBanner />}
      <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">{t('submit.title')}</h2>
        <p className="text-slate-600 text-sm mb-6">{t('submit.privacy')}</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <textarea
              rows={5}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={t('submit.placeholder')}
              className="w-full p-4 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-600 focus:border-brand-600 text-sm"
              maxLength={5000}
            />
            <div className="text-right text-xs text-slate-400 mt-1">{content.length} / 5000</div>
          </div>

          <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-sm">
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={ack}
                onChange={(e) => setAck(e.target.checked)}
                className="mt-1 h-4 w-4 rounded text-brand-600 focus:ring-brand-600"
              />
              <span className="text-slate-700">{t('submit.ack')}</span>
            </label>

            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={lostMoney}
                onChange={(e) => setLostMoney(e.target.checked)}
                className="mt-1 h-4 w-4 rounded text-red-600 focus:ring-red-600"
              />
              <span className="text-red-700 font-semibold">{t('submit.lostMoney')}</span>
            </label>
          </div>

          {error && <div className="text-red-600 text-sm">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white font-semibold py-3 px-4 rounded-xl transition shadow disabled:opacity-50"
          >
            {loading ? 'Analyzing Message...' : t('submit.button')}
          </button>
        </form>
      </div>
    </div>
  );
}