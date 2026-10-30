import React from 'react';
import { Check, AlertCircle, Clock, ShieldCheck } from 'lucide-react';

interface WorkflowStepperProps {
  currentStage: string;
  workflowStatus: string;
  stages?: string[];
}

const DEFAULT_STAGES = ['DRAFT', 'SCRUTINY', 'EVC', 'SAC_SHC', 'COMPLETED'];

const STAGE_LABELS: Record<string, string> = {
  DRAFT: 'Draft Submission',
  SCRUTINY: 'Scrutiny Review',
  EVC: 'EVC Inspection',
  SAC_SHC: 'SAC / SHC Committee',
  COMPLETED: 'Statutory Completion'
};

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  currentStage,
  workflowStatus,
  stages = DEFAULT_STAGES
}) => {
  const currentIndex = stages.indexOf(currentStage);

  return (
    <div className="w-full py-4 px-2">
      <div className="flex items-center justify-between relative">
        {stages.map((stage, idx) => {
          const isPassed = idx < currentIndex;
          const isCurrent = idx === currentIndex;
          const isFuture = idx > currentIndex;
          const isDeficient = isCurrent && workflowStatus === 'DEFICIENCY_RETURNED';
          const isCompleted = isCurrent && workflowStatus === 'STAGE_COMPLETED';

          let stepBg = 'bg-slate-200 text-slate-500';
          let borderColor = 'border-slate-300';
          let textColor = 'text-slate-500 font-normal';

          if (isPassed || isCompleted) {
            stepBg = 'bg-emerald-600 text-white';
            borderColor = 'border-emerald-600';
            textColor = 'text-emerald-900 font-semibold';
          } else if (isDeficient) {
            stepBg = 'bg-amber-500 text-white animate-pulse';
            borderColor = 'border-amber-500';
            textColor = 'text-amber-800 font-semibold';
          } else if (isCurrent) {
            stepBg = 'bg-blue-600 text-white ring-4 ring-blue-100';
            borderColor = 'border-blue-600';
            textColor = 'text-blue-900 font-bold';
          }

          return (
            <React.Fragment key={stage}>
              {/* Step Circle & Label */}
              <div className="flex flex-col items-center relative z-10">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${stepBg} ${borderColor}`}
                >
                  {isPassed || isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : isDeficient ? (
                    <AlertCircle className="w-5 h-5" />
                  ) : isCurrent ? (
                    <Clock className="w-5 h-5 animate-spin" style={{ animationDuration: '4s' }} />
                  ) : (
                    <span className="text-xs font-semibold">{idx + 1}</span>
                  )}
                </div>
                <span className={`text-xs mt-2 text-center max-w-[90px] leading-tight ${textColor}`}>
                  {STAGE_LABELS[stage] || stage}
                </span>
                {isDeficient && (
                  <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-medium mt-1">
                    Deficiency
                  </span>
                )}
              </div>

              {/* Connecting Line */}
              {idx < stages.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 transition-colors -mt-6 ${
                    idx < currentIndex ? 'bg-emerald-600' : 'bg-slate-200'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
