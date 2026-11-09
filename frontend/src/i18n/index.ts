import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('cybersathi-lang') : null;

i18n.use(initReactI18next).init({
  lng: saved || 'en',
  fallbackLng: 'en',
  resources: {
    en: {
      translation: {
        'app.title': 'Citizen CyberSathi',
        'app.subtitle': 'National Cyber Scam Intelligence & Phishing Verification',
        'nav.history': 'Scan History',
        'submit.title': 'Check Suspicious SMS, URL, or UPI Message',
        'submit.placeholder': 'Paste the suspicious SMS, WhatsApp message, link, or UPI handle here...',
        'submit.privacy': 'Privacy Guard: Your text is encrypted. Never share account passwords or OTPs.',
        'submit.ack': 'I confirm this is suspicious content for analysis.',
        'submit.lostMoney': 'I have lost money in this incident',
        'submit.button': 'Analyze Threat Now',
        'helpline.banner': 'EMERGENCY: Call the National Cybercrime Helpline immediately: 1930',
        'result.confidence': 'Confidence Level',
        'result.indicators': 'Extracted Indicators (Defanged for Safety)',
        'result.rules': 'Triggered Scam Heuristics',
        'result.disclaimer': 'No automated tool guarantees 100% safety. Never share bank PINs or OTPs.',
        'result.download': 'Download Evidence Dossier (PDF)',
        'history.title': 'Your Recent Scans',
        'history.empty': 'No local scan history found.',
        'history.delete': 'Delete',
        'assessment.confirmed_malicious': 'Confirmed Malicious: Matches verified fraud database.',
        'assessment.high_risk': 'High Risk: Multiple scam heuristics detected.',
        'assessment.suspicious': 'Suspicious: Exercise caution. Avoid clicking links.',
        'assessment.no_known_threat': 'No Known Threat: No scam markers detected (Disclaimers apply).',
        'assessment.inconclusive': 'Inconclusive: Unable to reach definitive classification.',
      },
    },
    hi: {
      translation: {
        'app.title': 'सिटिज़न साइबर साथी',
        'app.subtitle': 'राष्ट्रीय साइबर फ्रॉड अलर्ट और संदिग्ध संदेश जांच मंच',
        'nav.history': 'स्कैन इतिहास',
        'submit.title': 'संदिग्ध SMS, लिंक या UPI संदेश की जाँच करें',
        'submit.placeholder': 'संदिग्ध SMS, व्हाट्सएप संदेश, वेबसाइट लिंक या UPI यहाँ पेस्ट करें...',
        'submit.privacy': 'गोपनीयता सुरक्षा: सामग्री एन्क्रिप्ट की जाती है। कभी भी पासवर्ड या OTP साझा न करें।',
        'submit.ack': 'मैं पुष्टि करता/करती हूँ कि यह विश्लेषण हेतु संदिग्ध सामग्री है।',
        'submit.lostMoney': 'इस घटना में मेरा वित्तीय नुकसान (पैसा कट) हुआ है',
        'submit.button': 'अभी जाँच करें',
        'helpline.banner': 'आपातकालीन सूचना: तुरंत राष्ट्रीय साइबर हेल्पलाइन 1930 पर कॉल करें।',
        'result.confidence': 'विश्वसनीयता स्तर',
        'result.indicators': 'निकाले गए संकेतक (सुरक्षा हेतु Defanged)',
        'result.rules': 'पहचाने गए फ्रॉड संकेत',
        'result.disclaimer': 'यह आकलन पूर्ण सुरक्षा की गारंटी नहीं है। कभी भी OTP या पिन साझा न करें।',
        'result.download': 'शिकायत साक्ष्य रिपोर्ट (PDF) डाउनलोड करें',
        'history.title': 'आपका स्कैन इतिहास',
        'history.empty': 'कोई पिछला रिकॉर्ड नहीं मिला।',
        'history.delete': 'हटाएं',
        'assessment.confirmed_malicious': 'सत्यापित ख़तरा: यह सामग्री फ्रॉड रिकॉर्ड से मेल खाती है।',
        'assessment.high_risk': 'अत्यधिक संदिग्ध: धोखाधड़ी के कई संकेत मिले हैं।',
        'assessment.suspicious': 'सावधानी बरतें: संदिग्ध संकेत मौजूद हैं। लिंक न खोलें।',
        'assessment.no_known_threat': 'कोई ज्ञात ख़तरा नहीं मिला (सावधानी आवश्यक है)।',
        'assessment.inconclusive': 'अनिर्णायक: स्पष्ट निष्कर्ष नहीं निकाला जा सका।',
      },
    },
  },
});

export default i18n;