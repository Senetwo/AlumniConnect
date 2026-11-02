
import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Search,
  ExternalLink,
  Code2,
  Cloud,
  BriefcaseBusiness,
} from "lucide-react";
import Navbar from "../components/Navbar";


const categoryIcons = {
  "Technical Skills": Code2,
  "Cloud Computing": Cloud,
  "Career Development": BriefcaseBusiness,
};

function getSourceLabel(resourceUrl) {
  try {
    return new URL(resourceUrl).hostname.replace(/^www\./, "");
  } catch {
    return "External source";
  }
}

export default function KnowledgePage() {
  const [resources, setResources] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadAttempt, setLoadAttempt] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadResources() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/knowledge/"
        );

        if (!response.ok) {
          throw new Error("Unable to load learning resources.");
        }

        const data = await response.json();

        if (active) {
          setResources(data);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Unable to load resources.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadResources();

    return () => {
      active = false;
    };
  }, [loadAttempt]);

  const availableCategories = useMemo(
    () => [
      "All",
      ...new Set(resources.map((resource) => resource.category)),
    ],
    [resources]
  );

  const filteredResources = useMemo(() => {
    const query = search.trim().toLowerCase();

    return resources.filter((resource) => {
      const matchesCategory =
        category === "All" || resource.category === category;

      const matchesSearch =
        !query ||
        [
          resource.title,
          resource.description,
          resource.category,
          resource.resource_type,
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);

      return matchesCategory && matchesSearch;
    });
  }, [resources, search, category]);

  return (
    <div className="app">
      <Navbar />
      <main className="app-content-page knowledge-page">
      <section className="content-page-hero knowledge-hero">
        <div className="knowledge-hero-kicker">
          <BookOpen className="h-5 w-5" />
          AlumniConnect Knowledge Hub
        </div>

        <h1>
          Learn, grow, and move your career forward.
        </h1>

        <p>
          Discover technical learning, cloud training, and professional
          development resources selected to support your next career step.
        </p>

        <label className="knowledge-search">
          <Search size={19} aria-hidden="true" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search skills, cloud, career resources..."
            aria-label="Search learning resources"
            className="knowledge-search-input"
          />
          <span className="visually-hidden">Search learning resources</span>
        </label>
      </section>

      <section className="content-page-section">
        <div className="knowledge-section-heading">
          <div>
            <span className="eyebrow">CURATED FOR YOUR NEXT STEP</span>
            <h2>Explore resources</h2>
          </div>
          <p className="knowledge-results-count">
            {filteredResources.length} resource
            {filteredResources.length === 1 ? "" : "s"} found
          </p>
        </div>

        <div className="knowledge-filters" aria-label="Filter by category">
          {availableCategories.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setCategory(item)}
              aria-pressed={category === item}
              className={`knowledge-filter ${category === item ? "is-active" : ""}`}
            >
              {item}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="knowledge-loading" role="status" aria-label="Loading resources">
            {[1, 2, 3].map((item) => <div className="knowledge-skeleton" key={item} />)}
          </div>
        ) : error ? (
          <div role="alert" className="knowledge-empty-state knowledge-error-state">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => setLoadAttempt((attempt) => attempt + 1)}
              className="btn btn-outline"
            >
              Try again
            </button>
          </div>
        ) : filteredResources.length === 0 ? (
          <div className="knowledge-empty-state">
            <Search size={30} aria-hidden="true" />
            <h3>
              No matching resources
            </h3>
            <p>
              Try another search or category, or check back after resources
              have been published.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setCategory("All");
              }}
              className="btn btn-outline"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="content-card-grid">
            {filteredResources.map((resource) => {
              const Icon = categoryIcons[resource.category] || BookOpen;

              return (
                <article
                  key={resource.id}
                  className="content-card knowledge-resource-card"
                >
                  <div className="knowledge-card-top">
                    <div className="knowledge-resource-icon">
                      <Icon size={20} aria-hidden="true" />
                    </div>
                    <span className="knowledge-category-tag">
                      {resource.category}
                    </span>
                  </div>

                  <h3>
                    {resource.title}
                  </h3>

                  <p className="knowledge-description">
                    {resource.description}
                  </p>

                  <p className="knowledge-source">
                    Source: {resource.source_name || getSourceLabel(resource.url)}
                    {resource.source_author && <span>By {resource.source_author}</span>}
                    <span>{resource.publication_date ? new Date(`${resource.publication_date}T00:00:00`).toLocaleDateString() : "Publication date not provided"}</span>
                  </p>

                  <div className="knowledge-card-footer">
                    <p>
                      {resource.resource_type} · External resource
                    </p>
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="knowledge-resource-link"
                    >
                      Explore resource
                      <ExternalLink size={16} />
                    </a>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <p className="knowledge-footnote">
        Resources are provided by external organisations. Availability,
        fees, and content may change.
      </p>
      </main>
    </div>
  );
}

