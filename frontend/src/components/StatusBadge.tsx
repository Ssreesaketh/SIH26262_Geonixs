import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'stage' | 'workflow' | 'document' | 'severity';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'workflow' }) => {
  const s = (status || '').toUpperCase();

  let badgeClass = 'badge-neutral';
  let label = status;

  if (['CRITICAL', 'OVERDUE', 'EXPIRED', 'DEFICIENCY_RETURNED', 'RECOMMENDED_REJECTION'].includes(s)) {
    badgeClass = 'badge-critical';
  } else if (['WARNING', 'UPCOMING_SLA', 'EXPIRING_SOON', 'RETURNED_FOR_CORRECTION'].includes(s)) {
    badgeClass = 'badge-warning';
  } else if (['STAGE_COMPLETED', 'VERIFIED', 'VALID', 'RECOMMENDED_APPROVAL', 'COMPLETED'].includes(s)) {
    badgeClass = 'badge-success';
  } else if (['UNDER_REVIEW', 'SUBMITTED', 'SCHEDULED'].includes(s)) {
    badgeClass = 'badge-neutral';
  }

  // Format label for readability
  label = s.replace(/_/g, ' ');

  return (
    <span className={`badge ${badgeClass}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70"></span>
      {label}
    </span>
  );
};
