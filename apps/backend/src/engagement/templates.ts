export interface NotificationTemplate {
  category: string;
  priority: string;
  titleTemplate: string;
  messageTemplate: string;
}

export const NOTIFICATION_TEMPLATES: Record<string, NotificationTemplate> = {
  UPCOMING_JOURNEY: {
    category: 'Journey',
    priority: 'high',
    titleTemplate: 'Upcoming Journey Reminder: {src} to {dest}',
    messageTemplate: 'Hi {name}, this is a reminder for your train journey from {src} to {dest} on {date} at {time}. Prep details are ready in your dashboard.',
  },
  JOURNEY_PREPARATION: {
    category: 'Journey',
    priority: 'medium',
    titleTemplate: 'Travel Checklist for {src} ➔ {dest}',
    messageTemplate: 'Hello {name}! Do not forget your digital ID, tickets, and check the weather advisory before boarding today.',
  },
  PNR_STATUS_CHANGE: {
    category: 'PNR',
    priority: 'high',
    titleTemplate: 'PNR Alert: Status Change on {pnr}',
    messageTemplate: 'Good news! PNR {pnr} waitlist position has updated. Booking status is now: {status}.',
  },
  AI_WEEKLY_INSIGHT: {
    category: 'AI',
    priority: 'low',
    titleTemplate: 'AI Travel Insights for {name}',
    messageTemplate: 'Based on your recent trips, you could save up to 20% on fares by booking 10 days earlier on the NDLS-BPL corridor.',
  },
  BILLING_SUCCESS: {
    category: 'Billing',
    priority: 'medium',
    titleTemplate: 'Payment Success: Plan {planName} Activated',
    messageTemplate: 'Thank you! Your transaction for Rs. {amount} has cleared. Invoice {invoiceNum} is ready for download.',
  },
  BILLING_FAILED: {
    category: 'Billing',
    priority: 'high',
    titleTemplate: 'Payment Action Required: Renewal Failed',
    messageTemplate: 'Alert: Your subscription transaction of Rs. {amount} failed to settle. Please update payment credentials.',
  },
  SYSTEM_QUOTA_WARN: {
    category: 'System',
    priority: 'medium',
    titleTemplate: 'AI Quota Usage Alert: {used}% Expired',
    messageTemplate: 'Warning: You have consumed {used}% of your active monthly AI credits limits.',
  },
};

export function renderTemplate(
  templateKey: string,
  variables: Record<string, string | number>
): { title: string; message: string; category: string; priority: string } {
  const tpl = NOTIFICATION_TEMPLATES[templateKey];
  if (!tpl) {
    return {
      title: 'RailYatra Update',
      message: 'You have a new update in your dashboard.',
      category: 'System',
      priority: 'medium',
    };
  }

  let title = tpl.titleTemplate;
  let message = tpl.messageTemplate;

  for (const [key, val] of Object.entries(variables)) {
    title = title.replace(new RegExp(`{${key}}`, 'g'), String(val));
    message = message.replace(new RegExp(`{${key}}`, 'g'), String(val));
  }

  return {
    title,
    message,
    category: tpl.category,
    priority: tpl.priority,
  };
}
