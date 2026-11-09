import { z } from 'zod';

const BASE = import.meta.env.VITE_API_BASE_URL || '';

export const ScanResponseSchema = z.object({
  scan_id: z.string(),
  status: z.string(),
  reported_financial_loss: z.boolean(),
  classification: z.string().optional(),
  confidence: z.string().optional(),
  rule_ids: z.array(z.string()).optional(),
  indicators: z.array(z.object({ type: z.string(), value: z.string() })).optional(),
  technical_evidence: z.record(z.any()).optional(),
  social_engineering_evidence: z.record(z.any()).optional(),
  disclaimer: z.string().optional(),
});

export type ScanResponse = z.infer<typeof ScanResponseSchema>;

export async function createScan(content: string, lostMoney: boolean): Promise<ScanResponse> {
  const res = await fetch(`${BASE}/api/v1/scans`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': crypto.randomUUID(),
    },
    body: JSON.stringify({
      raw_content: content,
      reported_financial_loss: lostMoney,
      channel: 'web',
    }),
  });
  if (!res.ok) throw new Error('Failed to analyze scan');
  return ScanResponseSchema.parse(await res.json());
}

export async function getScan(scanId: string): Promise<ScanResponse> {
  const res = await fetch(`${BASE}/api/v1/scans/${scanId}`);
  if (!res.ok) throw new Error('Scan not found');
  return ScanResponseSchema.parse(await res.json());
}

export async function deleteScan(scanId: string): Promise<void> {
  const res = await fetch(`${BASE}/api/v1/scans/${scanId}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 404) throw new Error('Deletion failed');
}

export async function getReportUrl(scanId: string): Promise<string> {
  const res = await fetch(`${BASE}/api/v1/scans/${scanId}/report.pdf`);
  if (!res.ok) throw new Error('Failed to get report token');
  const data = await res.json();
  return `${BASE}${data.url}`;
}

export function defang(url: string): string {
  return url.replace(/http/g, 'hxxp').replace(/\./g, '[.]');
}