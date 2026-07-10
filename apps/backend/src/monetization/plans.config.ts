export interface PlanEntitlements {
  tierName: string;
  price: number;
  currency: string;
  monthlyCredits: number;        // AI Analysis credits
  dailyMessagesLimit: number;    // AI chat messages
  pnrMonitorLimit: number;
  savedRoutesLimit: number;
  features: string[];
}

export const SUBSCRIPTION_PLANS: Record<string, PlanEntitlements> = {
  FREE: {
    tierName: 'Free Sandbox',
    price: 0,
    currency: 'INR',
    monthlyCredits: 3,
    dailyMessagesLimit: 10,
    pnrMonitorLimit: 2,
    savedRoutesLimit: 3,
    features: ['Basic AI Chat', 'Waitlist Predictor (3 runs)', '2 Active PNR Statuses'],
  },
  PREMIUM: {
    tierName: 'Premium Travel',
    price: 299,
    currency: 'INR',
    monthlyCredits: 30,
    dailyMessagesLimit: 100,
    pnrMonitorLimit: 20,
    savedRoutesLimit: 20,
    features: ['Superfast AI Chat', 'Journey Intelligence Engine Cockpit', 'Alternate Date & Boarding suggestions', 'SMS Delay Notifications', '20 Active PNR Monitoring slots'],
  },
  PREMIUM_PLUS: {
    tierName: 'Premium Plus Pro',
    price: 599,
    currency: 'INR',
    monthlyCredits: 9999, // unlimited representation
    dailyMessagesLimit: 9999,
    pnrMonitorLimit: 9999,
    savedRoutesLimit: 9999,
    features: ['Dedicated AI Core Priority Node', 'Unlimited Waitlist clearances', 'Unlimited Boarding junction analysis', 'Priority WhatsApp/SMS Journey Notifications', 'Ad-Free desktop workspace'],
  },
};
