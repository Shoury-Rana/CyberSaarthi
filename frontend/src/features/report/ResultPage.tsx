import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getReportUrl, getScan } from '../../shared/api';
import DefangedIndicators from '../../shared/DefangedIndicators';
import HelplineBanner from '../../shared/HelplineBanner';

const BADGE_COLORS: Record<string, string> = {
  CONFIRMED_MALICIOUS: 'bg-red-100 text-red-800 border-red-300',
  HIGH_RISK: 'bg-orange-100 text-orange-800 border-orange-300',
  SUSPICIOUS: 'bg-amber-100 text-amber-800 border-amber-300',
  NO_KNOWN_THREAT_DETECTED: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  INCONCLUSIVE: 'bg-slate-100 text-slate-800 border-slate-300',
};

export default function ResultPage() {
  const { t } = useTranslation();
  const { scanId } = useParams();

  const { data: scan, isLoading, error } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => getScan(scanId!),
    enabled: Boolean(scanId),
  });

  const handleDownload = async () => {
    try {
      const url = await getReportUrl(scanId!);
      window.open(url, '_blank');
    } catch {
      alert('Could not download report.');
    }
  };

  if (isLoading) return <div className="text-center py-20">Loading analysis...</div>;
  if (error || !scan) return <div className="text-center py-20 text-red-600">Scan not found.</div>;

  const classification = scan.classification || 'INCONCLUSIVE';
  const badgeStyle = BADGE_COLORS[classification] || BADGE_COLORS.INCONCLUSIVE;

  // Use full extracted indicators (URLs, Domains, Phone, UPI)
  const indicatorValues: string[] = (scan.indicators || []).map((i: any) => i.value);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {scan.reported_financial_loss && <HelplineBanner />}

      <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6">
          <div>
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${badgeStyle} mb-2`}>
              {classification}
            </span>
            <h1 className="text-2xl font-extrabold text-slate-900">{t(`assessment.${classification.toLowerCase()}`)}</h1>
          </div>
          <button
            onClick={handleDownload}
            className="bg-brand-600 hover:bg-brand-700 text-white px-5 py-2.5 rounded-xl font-medium text-sm transition shadow flex items-center gap-2 justify-center"
          >
            {t('result.download')}
          </button>
        </div>

        <div>
          <h3 className="font-semibold text-slate-800 mb-1">{t('result.confidence')}</h3>
          <p className="text-sm text-slate-600">{scan.confidence || 'LOW'}</p>
        </div>

        {scan.rule_ids && scan.rule_ids.length > 0 && (
          <div>
            <h3 className="font-semibold text-slate-800 mb-2">{t('result.rules')}</h3>
            <div className="flex flex-wrap gap-2">
              {scan.rule_ids.map((r) => (
                <span key={r} className="bg-slate-100 text-slate-700 text-xs font-mono px-2.5 py-1 rounded border border-slate-200">
                  {r}
                </span>
              ))}
            </div>
          </div>
        )}

        <DefangedIndicators items={indicatorValues} />

        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 space-y-1">
          <p className="font-semibold text-slate-700">Notice:</p>
          <p>{scan.disclaimer || t('result.disclaimer')}</p>
        </div>

        <div className="flex justify-between items-center pt-2">
          <Link to="/" className="text-sm font-semibold text-brand-600 hover:text-brand-800">
            ← Analyze Another Message
          </Link>
          <Link to={`/scan/${scanId}/report`} className="text-sm font-semibold text-slate-600 hover:text-slate-800">
            View Evidence Dossier →
          </Link>
        </div>
      </div>
    </div>
  );
}