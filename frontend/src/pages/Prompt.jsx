'use client'

import { useState } from 'react';
import { Dialog, DialogPanel } from '@headlessui/react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

export default function Prompt() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [attempts, setAttempts] = useState(3);
  const [language, setLanguage] = useState('Python');

  // Function to send data to backend
  const sendPromptToBackend = async () => {
    try {
      const response = await axios.post('/start_agent/', {
        explanation: prompt,
        max_attempts: attempts,
        language: language,
      });

      console.log(response.data); // Log response from backend
      window.location.href = `/ide?data=${encodeURIComponent(JSON.stringify(response.data))}`; // Redirect to IDE page with response data
    } catch (error) {
      console.error("Error sending data:", error);
    }
  };

  return (
    <div className="bg-white">
      <header className="absolute inset-x-0 top-0 z-50">
        <nav aria-label="Global" className="flex items-center justify-between p-6 lg:px-8">
          <div className="flex lg:flex-1">
            <a href="#" className="-m-1.5 p-1.5">
              <span className="sr-only">Your Company</span>
              <img
                alt=""
                src="https://tailwindui.com/plus-assets/img/logos/mark.svg?color=indigo&shade=600"
                className="h-8 w-auto"
              />
            </a>
          </div>
        </nav>
      </header>

      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-28 lg:py-36">
          <div className="text-center">
            <h1 className="text-5xl font-semibold tracking-tight text-gray-900 sm:text-7xl">
              What would you like to learn today?
            </h1>
            <p className="mt-8 text-md font-medium text-gray-500 sm:text-xl">
              Enter your topic or question below and let us guide your learning journey.
            </p>

            <div className="mt-10 flex flex-col items-center gap-y-4">
              {/* Textarea for user input */}
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter what you want to learn..."
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                rows={4}
              />

              {/* Select attempts */}
              <p className="mt-4 text-md font-medium text-gray-500 sm:text-xl">
                How many attempts do you want to make before the solution is shown?
              </p>
              <select
                className="w-1/2 rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                value={attempts}
                onChange={(e) => setAttempts(parseInt(e.target.value))}
              >
                {[...Array(10).keys()].map((num) => (
                  <option key={num + 1} value={num + 1}>{num + 1}</option>
                ))}
              </select>

              {/* Select language */}
              <p className="mt-4 text-md font-medium text-gray-500 sm:text-xl">
                Which programming language do you want to use?
              </p>
              <select
                className="w-1/2 rounded-lg border border-gray-300 px-4 py-3 text-gray-900 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {["Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Swift", "Kotlin"].map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>

              {/* Button to send data to backend */}
              <button
                onClick={sendPromptToBackend}
                className="rounded-md mt-4 bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none"
              >
                Start Learning
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
