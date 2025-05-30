import React from 'react';

interface Step {
  id: string;
  name: string;
  description: string;
  status: 'complete' | 'current' | 'upcoming';
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: string;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({ steps, currentStep }) => {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center">
        {steps.map((step, stepIdx) => (
          <li key={step.id} className={stepIdx !== steps.length - 1 ? 'relative flex-1' : 'relative'}>
            <div className="flex items-center">
              <div className="relative flex h-10 w-10 items-center justify-center">
                {step.status === 'complete' ? (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                    <svg
                      className="h-6 w-6 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                ) : step.status === 'current' ? (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-blue-600 bg-white dark:bg-gray-800">
                    <span className="text-blue-600 font-semibold">{stepIdx + 1}</span>
                  </div>
                ) : (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800">
                    <span className="text-gray-500 dark:text-gray-400">{stepIdx + 1}</span>
                  </div>
                )}
              </div>
              <div className="ml-4 min-w-0 flex-1">
                <p
                  className={`text-sm font-medium ${
                    step.status === 'current'
                      ? 'text-blue-600 dark:text-blue-400'
                      : step.status === 'complete'
                      ? 'text-gray-900 dark:text-white'
                      : 'text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {step.name}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{step.description}</p>
              </div>
            </div>
            {stepIdx !== steps.length - 1 && (
              <div className="absolute top-5 right-0 hidden h-0.5 w-full bg-gray-200 dark:bg-gray-700 sm:block">
                <div
                  className={`h-0.5 bg-blue-600 transition-all duration-500 ${
                    step.status === 'complete' ? 'w-full' : 'w-0'
                  }`}
                />
              </div>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default StepIndicator; 