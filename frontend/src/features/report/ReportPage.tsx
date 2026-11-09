import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getReportUrl, getScan } from '../../shared/api';
import DefangedIndicators from '../../shared/DefangedIndicators';
import HelplineBanner from '../../shared/HelplineBanner';

export default function ReportPage() {
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

  if (isLoading) return <div className="text-center py-20">Loading evidence dossier...</div>;
  if (error || !scan) return <div className="text-center py-20 text-red-600">Scan not found.</div>;

  const indicatorValues: string[] = (scan.indicators || []).map((i: any) => i.value);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {scan.reported_financial_loss && <HelplineBanner />}

      <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6">
          <div>
            <span className="text-xs font-bold text-brand-700 bg-brand-50 px-2.5 py-1 rounded border border-brand-200 uppercase">
              Official Evidence Dossier
            </span>
            <h1 className="text-2xl font-black text-slate-900 mt-2">
              Cyber Fraud Evidence &amp; Complaint Preparation Report
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Intended for submission on <b>cybercrime.gov.in</b> (Helpline: 1930)
            </p>
          </div>
          <button
            onClick={handleDownload}
            className="bg-brand-600 hover:bg-brand-700 text-white px-5 py-2.5 rounded-xl font-medium text-sm transition shadow flex items-center gap-2 justify-center"
          >
            {t('result.download')}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
          <div>
            <span className="text-slate-400 font-semibold block">SCAN ID</span>
            <span className="font-mono text-slate-700">{scan.scan_id}</span>
          </div>
          <div>
            <span className="text-slate-400 font-semibold block">CLASSIFICATION</span>
            <span className="font-bold text-slate-800">{scan.classification || 'INCONCLUSIVE'}</span>
          </div>
        </div>

        <DefangedIndicators items={indicatorValues} />

        <div className="space-y-3">
          <h3 className="font-bold text-slate-800 text-sm">Filing Instructions (National Cybercrime Portal)</h3>
          <ol className="list-decimal list-inside space-y-1.5 text-xs text-slate-600 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <li>Visit <b>cybercrime.gov.in</b> and select "Report Cyber Crime".</li>
            <li>If money was lost, call <b>1930</b> immediately to register the transaction with your bank.</li>
            <li>Attach the downloaded PDF report as supporting documentary evidence.</li>
            <li>Provide transaction UTR and screenshot evidence of the suspect handle.</li>
          </ol>
        </div>

        <div className="flex justify-between items-center pt-4 border-t">
          <Link to={`/scan/${scanId}/result`} className="text-sm font-semibold text-brand-600 hover:underline">
            ← Back to Assessment
          </Link>
          <button
            onClick={() => window.print()}
            className="text-sm font-semibold text-slate-600 hover:text-slate-900 border border-slate-300 px-3 py-1.5 rounded-lg"
          >
            Print Dossier
          </button>
        </div>
      </div>
    </div>
  );
}