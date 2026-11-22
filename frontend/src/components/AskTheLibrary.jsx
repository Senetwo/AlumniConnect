import { useState } from "react";
import { ExternalLink, Sparkles } from "lucide-react";
import { apiRequest } from "../services/api";

const MIN_LENGTH = 3;
const MAX_LENGTH = 500;

export default function AskTheLibrary() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [asking, setAsking] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const text = question.trim();
    if (text.length < MIN_LENGTH || asking) return;

    setAsking(true);
    setError("");
    setResult(null);

    try {
      setResult(
        await apiRequest("/api/knowledge/ask", {
          method: "POST",
          body: JSON.stringify({ question: text }),
        })
      );
    } catch (err) {
      setError(err.message || "The library assistant could not answer. Please try again.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <section className="content-page-section ask-library" aria-labelledby="ask-library-title">
      <div className="knowledge-section-heading">
        <div>
          <span className="eyebrow">ASK THE LIBRARY</span>
          <h2 id="ask-library-title">Get an answer from our resources</h2>
        </div>
      </div>

      <form className="ask-library-form" onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="ask-library-input">
          Your question
        </label>
        <input
          id="ask-library-input"
          type="text"
          value={question}
          maxLength={MAX_LENGTH}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="For example: How should I prepare for a technical interview?"
          className="ask-library-input"
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={asking || question.trim().length < MIN_LENGTH}
        >
          <Sparkles size={16} aria-hidden="true" />
          {asking ? "Searching..." : "Ask"}
        </button>
      </form>

      <div className="ask-library-result" aria-live="polite">
        {error && (
          <p role="alert" className="ask-library-error">
            {error}
          </p>
        )}

        {result && (
          <article className="ask-library-answer">
            <p>{result.answer}</p>

            {result.grounded && result.sources.length > 0 && (
              <>
                <h3>Sources</h3>
                <ul>
                  {result.sources.map((source) => (
                    <li key={`${source.type}-${source.id}`}>
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                          {source.title}
                          <ExternalLink size={14} aria-hidden="true" />
                        </a>
                      ) : (
                        <span>{source.title} (announcement)</span>
                      )}
                    </li>
                  ))}
                </ul>
              </>
            )}

            <p className="ask-library-note">
              {result.generated
                ? "AI-generated from library content. Check the sources before relying on it."
                : result.grounded
                  ? "These are the closest resources in the library, shown as written. Open the sources for the full details."
                  : "Try rephrasing your question, or browse the resources below."}
            </p>
          </article>
        )}
      </div>
    </section>
  );
}
