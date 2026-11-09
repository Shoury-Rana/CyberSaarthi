import { useTranslation } from 'react-i18next';

export default function HelplineBanner() {
  const { t } = useTranslation();
  return (
    <div className="bg-red-600 text-white p-4 rounded-xl shadow-md mb-6 flex flex-col md:flex-row items-center justify-between gap-3">
      <div>
        <h3 className="font-bold text-lg">{t('helpline.banner')}</h3>
        <p className="text-red-100 text-sm">
          National Cybercrime Reporting Helpline & Immediate Golden-Hour Financial Intervention.
        </p>
      </div>
      <a
        href="tel:1930"
        className="bg-white text-red-700 font-extrabold px-6 py-2.5 rounded-lg text-xl hover:bg-red-50 transition shadow"
      >
        DIAL 1930
      </a>
    </div>
  );
}