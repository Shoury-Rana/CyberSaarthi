import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getScan } from '../../shared/api';

export default function ScanStatusPage() {
  const { scanId } = useParams();
  const navigate = useNavigate();

  const { data } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => getScan(scanId!),
    enabled: Boolean(scanId),
  });

  useEffect(() => {
    if (data?.status === 'COMPLETED') {
      navigate(`/scan/${scanId}/result`, { replace: true });
    }
  }, [data, navigate, scanId]);

  return (
    <div className="max-w-md mx-auto text-center py-20 px-4">
      <div className="animate-spin h-10 w-10 border-4 border-brand-600 border-t-transparent rounded-full mx-auto mb-4"></div>
      <h2 className="text-xl font-bold text-slate-800">Processing Investigation</h2>
      <p className="text-slate-500 text-sm mt-1">Executing synchronous heuristic classification...</p>
    </div>
  );
}