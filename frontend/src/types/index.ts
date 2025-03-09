export interface Step {
  id: string;
  type: string;
  content: string;
  code?: string;
  hints?: string[];
  expectedOutput?: string;
}

export interface LearningStepProps {
  step: Step;
  onNext: () => void;
  onPrevious: () => void;
  isFirst: boolean;
  isLast: boolean;
} 