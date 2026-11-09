import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { defang } from './api';

export default function DefangedIndicators({ items }: { items: string[] }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  if (!items.length) return null;

  const defangedItems = items.map((i) => defang(i));

  const copyAll = async () => {
    await navigator.clipboard.writeText(defangedItems.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-4 bg-slate-100 p-4 rounded-xl border border-slate-200">
      <div className="flex justify-between items-center mb-2">
        <h4 className="font-semibold text-slate-800 text-sm">{t('result.indicators')}</h4>
        <button
          onClick={copyAll}
          className="text-xs bg-white border border-slate-300 px-2 py-1 rounded hover:bg-slate-50 text-slate-700 font-medium"
        >
          {copied ? 'Copied!' : 'Copy Defanged'}
        </button>
      </div>
      <div className="space-y-1 font-mono text-xs">
        {defangedItems.map((val, idx) => (
          <div key={idx} className="bg-white p-2 rounded border border-slate-200 break-all text-slate-700">
            {val}
          </div>
        ))}
      </div>
    </div>
  );
}