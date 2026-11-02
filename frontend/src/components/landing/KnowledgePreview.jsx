import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ExternalLink } from "lucide-react";
import { apiRequest } from "../../services/api";

const PREVIEW_COUNT = 4;

// Shows real, published Knowledge Hub resources. If the list can't be loaded
// or is empty the section is not rendered at all: nothing is invented.
export default function KnowledgePreview() {
  const [resources, setResources] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest("/api/knowledge/", { signal: controller.signal })
      .then((data) => setResources(Array.isArray(data) ? data.slice(0, PREVIEW_COUNT) : []))
      .catch((error) => {
        if (error.name !== "AbortError") setResources([]);
      });
    return () => controller.abort();
  }, []);

  if (resources && resources.length === 0) return null;

  return (
    <section className="lp-section" id="knowledge-hub" aria-labelledby="knowledge-title" aria-busy={resources === null}>
      <div className="lp-section-head lp-section-head-row">
        <div>
          <span className="lp-eyebrow lp-eyebrow-red">KNOWLEDGE HUB</span>
          <h2 id="knowledge-title">Learning worth passing on.</h2>
          <p>Practical resources shared to support ongoing professional growth.</p>
        </div>
        <Link to="/knowledge" className="lp-text-link">
          Browse all resources <ArrowRight size={16} aria-hidden="true" />
        </Link>
      </div>

      <div className="lp-resources">
        {resources === null
          ? Array.from({ length: PREVIEW_COUNT }, (_, index) => <div className="lp-resource lp-resource-skeleton" key={index} aria-hidden="true" />)
          : resources.map((resource) => (
            <article className="lp-resource" key={resource.id}>
              <span className="lp-resource-category">{resource.category}</span>
              <h3>{resource.title}</h3>
              <p>{resource.description}</p>
              <div className="lp-resource-foot">
                <span>{[resource.resource_type, resource.source_name].filter(Boolean).join(" · ")}</span>
                <a href={resource.url} target="_blank" rel="noopener noreferrer">
                  Explore resource
                  <ExternalLink size={14} aria-hidden="true" />
                  <span className="visually-hidden"> (opens in a new tab)</span>
                </a>
              </div>
            </article>
          ))}
      </div>
    </section>
  );
}
