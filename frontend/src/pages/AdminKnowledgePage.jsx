
import { useCallback, useEffect, useState } from "react";
import { BookOpen, Pencil, Plus, Trash2, X, ExternalLink } from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";

const API_PATH = "/api/knowledge";

const emptyForm = {
  title: "",
  description: "",
  category: "Technical Skills",
  resource_type: "Learning platform",
  url: "",
  source_name: "",
  source_author: "",
  publication_date: "",
  is_published: false,
};

export default function AdminKnowledgePage() {
  const [resources, setResources] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // apiRequest attaches the current sign-in (password or Clerk) and refreshes it when needed.
  const request = useCallback((path = "", options = {}) => apiRequest(`${API_PATH}${path}`, options), []);

  const loadResources = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await request("/admin");
      setResources(data);
    } catch (err) {
      setError(err.message || "Could not load resources.");
    } finally {
      setLoading(false);
    }
  }, [request]);

  useEffect(() => {
    queueMicrotask(() => { void loadResources(); });
  }, [loadResources]);

  function updateField(event) {
    const { name, value, type, checked } = event.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function startEditing(resource) {
    setEditingId(resource.id);
    setForm({
      title: resource.title,
      description: resource.description,
      category: resource.category,
      resource_type: resource.resource_type,
      url: resource.url,
      source_name: resource.source_name || "",
      source_author: resource.source_author || "",
      publication_date: resource.publication_date || "",
      is_published: resource.is_published,
    });
    setError("");
    setSuccess("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const path = editingId !== null ? `/${editingId}` : "/";
      const method = editingId !== null ? "PATCH" : "POST";

      await request(path, {
        method,
        body: JSON.stringify({
          ...form,
          title: form.title.trim(),
          description: form.description.trim(),
          category: form.category.trim(),
          resource_type: form.resource_type.trim(),
          url: form.url.trim(),
          source_name: form.source_name.trim() || null,
          source_author: form.source_author.trim() || null,
          publication_date: form.publication_date || null,
        }),
      });

      setSuccess(
        editingId !== null
          ? "Resource updated successfully."
          : "Resource created successfully."
      );

      resetForm();
      await loadResources();
    } catch (err) {
      setError(err.message || "Could not save resource.");
    } finally {
      setSaving(false);
    }
  }

  async function togglePublished(resource) {
    setError("");
    setSuccess("");

    try {
      await request(`/${resource.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          is_published: !resource.is_published,
        }),
      });

      setSuccess(
        resource.is_published
          ? "Resource unpublished."
          : "Resource published."
      );

      await loadResources();
    } catch (err) {
      setError(err.message || "Could not change publication status.");
    }
  }

  async function deleteResource(resource) {
    const confirmed = window.confirm(
      `Delete "${resource.title}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");

    try {
      await request(`/${resource.id}`, { method: "DELETE" });

      if (editingId === resource.id) resetForm();

      setSuccess("Resource deleted.");
      await loadResources();
    } catch (err) {
      setError(err.message || "Could not delete resource.");
    }
  }

  return (
    <div className="app">
      <Navbar />
      <main className="app-content-page admin-knowledge-page">
      <header className="content-page-heading">
        <div className="flex items-center gap-2 text-sm font-medium text-red-700">
          <BookOpen className="h-5 w-5" />
          Administration
        </div>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Knowledge Hub Manager
        </h1>
        <p className="mt-2 text-slate-600">
          Create, review, publish, and maintain learning resources.
        </p>
      </header>

      {error && (
        <div role="alert" className="content-alert content-alert-error">
          {error}
        </div>
      )}

      {success && (
        <div role="status" className="content-alert content-alert-success">
          {success}
        </div>
      )}

      <section className="content-panel">
        <div className="mb-5 flex items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-slate-900">
            {editingId !== null ? "Edit resource" : "Add a resource"}
          </h2>

          {editingId !== null && (
            <button
              type="button"
              onClick={resetForm}
              className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
            >
              <X className="h-4 w-4" />
              Cancel edit
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="content-form-grid">
            <label className="block text-sm font-medium text-slate-700">
              Resource title
              <input
                name="title"
                value={form.title}
                onChange={updateField}
                minLength={3}
                maxLength={200}
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
                placeholder="e.g. AWS Skill Builder"
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Resource URL
              <input
                name="url"
                type="url"
                value={form.url}
                onChange={updateField}
                required
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
                placeholder="https://example.com"
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Category
              <input
                name="category"
                value={form.category}
                onChange={updateField}
                required
                minLength={2}
                maxLength={100}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
                placeholder="Technical Skills"
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Resource type
              <input
                name="resource_type"
                value={form.resource_type}
                onChange={updateField}
                required
                minLength={2}
                maxLength={100}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
                placeholder="Learning platform"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">Source name<input name="source_name" value={form.source_name} onChange={updateField} maxLength={200} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" placeholder="Verified publisher or organisation" /></label>
            <label className="block text-sm font-medium text-slate-700">Source author<input name="source_author" value={form.source_author} onChange={updateField} maxLength={200} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" placeholder="Optional; enter only when verified" /></label>
            <label className="block text-sm font-medium text-slate-700">Publication date<input name="publication_date" type="date" value={form.publication_date} onChange={updateField} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" /><small className="mt-1 block text-slate-500">Leave empty when the original source does not provide a verified date.</small></label>
          </div>

          <label className="block text-sm font-medium text-slate-700">
            Description
            <textarea
              name="description"
              value={form.description}
              onChange={updateField}
              minLength={10}
              maxLength={5000}
              required
              rows={4}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5"
              placeholder="Explain what alumni can learn or do with this resource."
            />
          </label>

          <label className="flex items-center gap-3 text-sm text-slate-700">
            <input
              type="checkbox"
              name="is_published"
              checked={form.is_published}
              onChange={updateField}
              className="h-4 w-4 accent-red-700"
            />
            Publish immediately so it appears in the Knowledge Hub
          </label>

          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-lg bg-red-700 px-5 py-3 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-60"
          >
            {editingId !== null ? (
              <Pencil className="h-4 w-4" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            {saving ? "Saving..." : editingId !== null ? "Save changes" : "Add resource"}
          </button>
        </form>
      </section>

      <section className="content-page-section">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-slate-900">
            Existing resources
          </h2>
          <button
            type="button"
            onClick={loadResources}
            disabled={loading}
            className="text-sm font-semibold text-red-700 hover:underline disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <p className="py-8 text-slate-600">Loading resources...</p>
        ) : resources.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
            No resources have been added yet.
          </div>
        ) : (
          <div className="content-resource-list">
            {resources.map((resource) => (
              <article
                key={resource.id}
                className="content-resource-row"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-slate-900">
                      {resource.title}
                    </h3>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                      resource.is_published
                        ? "bg-green-100 text-green-800"
                        : "bg-amber-100 text-amber-800"
                    }`}>
                      {resource.is_published ? "Published" : "Draft"}
                    </span>
                  </div>

                  <p className="mt-1 text-sm text-slate-600">
                    {resource.category} · {resource.resource_type}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{resource.source_name || "Source not specified"}{resource.source_author ? ` · ${resource.source_author}` : ""}{resource.publication_date ? ` · ${resource.publication_date}` : " · No verified publication date"}</p>

                  <p className="mt-2 line-clamp-2 text-sm text-slate-500">
                    {resource.description}
                  </p>

                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-flex items-center gap-1 break-all text-xs text-red-700 hover:underline"
                  >
                    View source <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => startEditing(resource)}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50"
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    onClick={() => togglePublished(resource)}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50"
                  >
                    {resource.is_published ? "Unpublish" : "Publish"}
                  </button>

                  <button
                    type="button"
                    onClick={() => deleteResource(resource)}
                    aria-label={`Delete ${resource.title}`}
                    className="rounded-lg border border-red-200 p-2 text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
      </main>
    </div>
  );
}
