import { useCallback, useEffect, useState } from "react";
import { Send, ThumbsUp, Trash2 } from "lucide-react";
import { apiRequest } from "../../services/api";
import { initials, timeAgo } from "../../utils/format";

const MAX_LENGTH = 2000;

export default function Feed({ me }) {
  const [posts, setPosts] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [draft, setDraft] = useState("");
  const [posting, setPosting] = useState(false);

  const load = useCallback(async (beforeId) => {
    const params = new URLSearchParams();
    if (beforeId) params.set("before_id", beforeId);
    const data = await apiRequest(`/api/community/posts?${params}`);
    return data;
  }, []);

  useEffect(() => {
    let active = true;
    load()
      .then((data) => { if (active) { setPosts(data.items); setHasMore(data.has_more); } })
      .catch((requestError) => { if (active) setError(requestError.message || "Unable to load the feed."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [load]);

  async function loadMore() {
    try {
      const data = await load(posts[posts.length - 1]?.id);
      setPosts((current) => [...current, ...data.items]);
      setHasMore(data.has_more);
    } catch (requestError) { setError(requestError.message || "Unable to load more posts."); }
  }

  async function publish(event) {
    event.preventDefault();
    if (!draft.trim()) return;
    setPosting(true);
    setError("");
    try {
      const post = await apiRequest("/api/community/posts", { method: "POST", body: JSON.stringify({ body: draft.trim() }) });
      setPosts((current) => [post, ...current]);
      setDraft("");
    } catch (requestError) { setError(requestError.message || "Unable to publish your post."); }
    finally { setPosting(false); }
  }

  async function toggleLike(post) {
    try {
      const result = await apiRequest(`/api/community/posts/${post.id}/like`, { method: post.liked_by_me ? "DELETE" : "PUT" });
      setPosts((current) => current.map((item) => (item.id === post.id ? { ...item, ...result } : item)));
    } catch (requestError) { setError(requestError.message || "Unable to update your reaction."); }
  }

  async function remove(post) {
    if (!window.confirm("Delete this post? This cannot be undone.")) return;
    try {
      await apiRequest(`/api/community/posts/${post.id}`, { method: "DELETE" });
      setPosts((current) => current.filter((item) => item.id !== post.id));
    } catch (requestError) { setError(requestError.message || "Unable to delete the post."); }
  }

  return (
    <div className="cm-feed">
      <form className="cm-card cm-composer" onSubmit={publish}>
        <div className="cm-avatar" aria-hidden="true">{initials(me?.full_name)}</div>
        <div className="cm-composer-body">
          <label htmlFor="cm-draft" className="visually-hidden">Share an update with the community</label>
          <textarea
            id="cm-draft"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Share an update, a question or something you have learned…"
            maxLength={MAX_LENGTH}
            rows={3}
          />
          <div className="cm-composer-footer">
            <span>{draft.length}/{MAX_LENGTH}</span>
            <button type="submit" className="btn btn-primary" disabled={posting || !draft.trim()}>
              <Send size={16} aria-hidden="true" />{posting ? "Posting…" : "Post"}
            </button>
          </div>
        </div>
      </form>

      {error && <div role="alert" className="page-alert">{error}</div>}

      {loading ? (
        <div className="cm-card cm-skeleton" role="status" aria-label="Loading the community feed" />
      ) : posts.length === 0 ? (
        <div className="cm-card cm-empty">
          <h2>No posts yet</h2>
          <p>Be the first to share an update with the community.</p>
        </div>
      ) : posts.map((post) => (
        <article className="cm-card cm-post" key={post.id}>
          <header>
            <div className="cm-avatar" aria-hidden="true">{initials(post.author.full_name)}</div>
            <div className="cm-post-author">
              <strong>{post.author.full_name}</strong>
              <span>{[post.author.role, post.author.career_path].filter(Boolean).join(" · ")}</span>
              <time dateTime={post.created_at}>{timeAgo(post.created_at)}</time>
            </div>
            {post.can_delete && (
              <button type="button" className="cm-icon-button" onClick={() => remove(post)} aria-label="Delete this post" title="Delete post">
                <Trash2 size={16} aria-hidden="true" />
              </button>
            )}
          </header>
          <p className="cm-post-body">{post.body}</p>
          <div className="cm-post-actions">
            <button
              type="button"
              className={`cm-like ${post.liked_by_me ? "is-liked" : ""}`}
              aria-pressed={post.liked_by_me}
              onClick={() => toggleLike(post)}
            >
              <ThumbsUp size={16} aria-hidden="true" />
              {post.liked_by_me ? "Liked" : "Like"}
              {post.like_count > 0 && <span className="cm-like-count">{post.like_count}</span>}
            </button>
          </div>
        </article>
      ))}

      {hasMore && <button type="button" className="btn btn-outline cm-more" onClick={loadMore}>Show more posts</button>}
    </div>
  );
}
