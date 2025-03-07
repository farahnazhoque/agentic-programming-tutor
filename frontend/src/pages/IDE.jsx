import {javascript} from "@codemirror/lang-javascript"
import {EditorView, basicSetup} from "codemirror"
import {useEffect, useRef} from "react"
import {python} from "@codemirror/lang-python"
import { useParams } from "react-router-dom";
import { useLocation } from "react-router-dom";

export default function IDE() {
  const editorRef = useRef(null);
  const viewRef = useRef(null);
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const dataString = searchParams.get("data");
  const parsedData = dataString ? JSON.parse(decodeURIComponent(dataString)) : null;

  console.log("Parsed Data:", parsedData); // Debugging log

  const defaultCode = parsedData ? parsedData.boilerplate_code : "print('Hello, World!')";
  const summary = parsedData ? parsedData.summary : "";

  useEffect(() => {
    viewRef.current = new EditorView({
      doc: defaultCode,
      parent: editorRef.current,
      extensions: [
        basicSetup,
        python()
      ]
    });
  
    return () => {
      viewRef.current.destroy();
    };
  }, [parsedData]);
  
  return (
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
          {/* Summary Section */}
          <div className="mb-8 p-6 bg-gray-50 rounded-lg shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Summary</h2>
            <div className="prose">
              {summary.split('•').map((point, index) => (
                point.trim() && (
                  <div key={index} className="flex items-start mb-2">
                    <span className="mr-2">•</span>
                    <span>{point.trim()}</span>
                  </div>
                )
              ))}
            </div>
          </div>

          {/* Code Editor Section */}
          <div className="mb-4">
            <h2 className="text-xl font-semibold mb-4">Code Editor</h2>
            <div ref={editorRef} className="border rounded-lg shadow-sm"></div>
          </div>
          
          <button
            className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            onClick={() => {
              const code = viewRef.current.state.doc.toString();
              console.log(code);
            }}
          >
            Run Code
          </button>
        </div>

        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-[calc(100%-13rem)] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[calc(100%-30rem)]"
        >
          <div
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
            className="relative left-[calc(50%+3rem)] aspect-1155/678 w-[36.125rem] -translate-x-1/2 bg-linear-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%+36rem)] sm:w-[72.1875rem]"
          />
        </div>
      </div>
    </div>
  );
}