import React from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { CodeEditor } from './CodeEditor';

function LearningSteps({ step, onNext, onPrevious, isFirst, isLast }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
      className="max-w-5xl mx-auto px-4 py-8"
    >
      <div className="bg-white">
        <div className="relative isolate px-6 pt-14 lg:px-8">
          <div
            aria-hidden="true"
            className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
          >
            <div
              style={{
                clipPath:
                  'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
              }}
              className="relative left-[calc(50%-11rem)] aspect-1155/678 w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-linear-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
            />
          </div>
          <div className="mx-auto max-w-4xl py-8">
            <div
              className="prose prose-invert max-w-none mb-8 prose-headings:text-blue-400 prose-a:text-blue-400 prose-strong:text-blue-300"
              dangerouslySetInnerHTML={{ __html: step.content }}
            />
          </div>

          {step.code && (
            <div className="my-8">
              <CodeEditor initialCode={step.code} exercise={step.content} />
            </div>
          )}

          <div className="flex justify-between mt-8 pt-8 border-t border-gray-800">
            <button
              onClick={onPrevious}
              disabled={isFirst}
              className={`flex items-center px-6 py-3 rounded-xl text-sm font-medium transition-colors duration-200 ${
                isFirst
                  ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Previous
            </button>

            <button
              onClick={onNext}
              disabled={isLast}
              className={`flex items-center px-6 py-3 rounded-xl text-sm font-medium transition-colors duration-200 ${
                isLast
                  ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              Next
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

LearningSteps.propTypes = {
  step: PropTypes.shape({
    content: PropTypes.string.isRequired,
    code: PropTypes.string
  }).isRequired,
  onNext: PropTypes.func.isRequired,
  onPrevious: PropTypes.func.isRequired,
  isFirst: PropTypes.bool.isRequired,
  isLast: PropTypes.bool.isRequired
};

export default LearningSteps;
