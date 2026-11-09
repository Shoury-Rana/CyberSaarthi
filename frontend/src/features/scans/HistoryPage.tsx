import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { deleteScan } from '../../shared/api';
import { readHistory, removeHistory } from '../../shared/history';

export default function HistoryPage() {
  const { t } = useTranslation();
  const [history, setHistory] = useState(readHistory);

  const handleDelete = async (scanId: string) => {
    try {
      await deleteScan(scanId);
    } catch {
      // Local deletion fallback
    }
    removeHistory(scanId);
    setHistory(readHistory());
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold text-slate-900 mb-6">{t('history.title')}</h2>
      {!history.length ? (
        <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-500">
          {t('history.empty')}
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div
              key={item.scan_id}
              className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-sm"
            >
              <Link to={`/scan/${item.scan_id}/result`} className="hover:underline">
                <div className="font-mono text-xs text-slate-500">{item.scan_id.slice(0, 8)}...</div>
                <div className="font-bold text-sm text-slate-800">{item.classification || 'ANALYZED'}</div>
                <div className="text-xs text-slate-400">{new Date(item.date).toLocaleString()}</div>
              </Link>
              <button
                onClick={() => handleDelete(item.scan_id)}
                className="text-xs text-red-600 hover:text-red-800 border border-red-200 bg-red-50 px-2.5 py-1.5 rounded"
              >
                {t('history.delete')}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}