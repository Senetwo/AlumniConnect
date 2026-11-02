# AlumniConnect networking and content plan

## Original implementation gaps

- The profile schema originally had no directory visibility control and no alumni/former-employee member type.
- Mentorship chat was originally scoped to accepted mentorships and had no general-purpose connections, messaging, blocking, reporting, or throttling.
- Knowledge Hub entries are created and published by admins as external links. The data model has a creation timestamp, but no source publication date or author field. The frontend must not present the creation timestamp as the article's publication date.
- The Kenya Airways website has public News & Press Releases and KQ Blog pages. This repository has no configured source feed/API, source credentials, or documented republication permission. Link out to approved original content until those are confirmed.
- Notifications are user-scoped and currently support mentorship, booking, and chat activity. There is no organizational-announcement workflow or duplicate/rate policy.

## Implemented: opt-in member directory

The current account roles define directory eligibility as mentors and mentees. Former employees need an account and an explicit role policy before they are eligible. Visibility defaults to off and is controlled in Profile settings. The authenticated directory is paginated, supports career-area and skill filters, and only returns name, role, career area/path, experience, skills, bio, and profile photo. It excludes email, goals, certifications, and mentorship interests. The member directory UI is available from the authenticated navigation.

## Implemented: connections and expanded messaging

Connection requests have unique member pairs and request, accept, decline, cancel, and disconnect actions with participant authorization. Blocks hide members and disable both community and mentorship messaging. Members can report accounts; admins can review reports. Requests, reports, and messages have per-user daily/hourly caps. Community messages require an accepted connection, check block state on every read/write, and support bounded pagination. Existing mentorship chat authorization remains in place.

## Implemented: announcements

Admins can send a community-wide announcement. The app stores the announcement and creates a user-scoped notification for each current member; members can read it from their notifications inbox.

Mentorship notifications now cover the request lifecycle: the mentor receives a new mentee request, the mentee receives a pending confirmation, and approval or rejection sends a status-specific update. Opting a profile into the directory notifies other mentor and mentee accounts that a new member profile is available. Notification actions link to the relevant workspace, mentorship, booking, chat, or directory screen. The inbox also has role-aware back navigation.

## Knowledge source integration

Admin-curated links remain the content ingestion method until the organization approves a source, permitted metadata/excerpts, update frequency, and attribution format. Knowledge Hub entries now store optional source name, author, and publication date; authors/dates must be explicitly verified and are never inferred from the AlumniConnect creation timestamp. No full articles are copied. The Kenya Airways news/blog feed or API has not been integrated pending documented access and republication guidance.

## Remaining rollout work

- Decide whether former employees can register and which additional roles, if any, belong in the directory.
- Obtain source approval and feed/API/republication guidance before automating Kenya Airways content ingestion.
- Run authenticated manual browser checks for opt-in/out, connection decisions, block/report behavior, messaging, and admin announcements at desktop and mobile widths.
- Repository-wide frontend lint still has existing hook-rule and unused-variable errors in AdminDashboard, AvailabilityPage, BookingPage, LoginPage, MentorWorkspacePage, and NotificationsPage. The newly changed screens pass targeted ESLint.

## Implemented: community home (feed, events, job opportunities)

The Community Directory page is now a LinkedIn-style home: a profile card, a tabbed centre column (Community feed, Members) and a right column with upcoming events and job opportunities.

- **Posts:** every member can post (up to 2000 characters, 10 per day), like and unlike, and delete their own posts. Admins can delete any post. Blocked members never see each other's posts.
- **Events:** admins create and cancel events at `/admin/community`. Members RSVP in the app and see a live "going" count. Times are entered and shown in East Africa Time. Past and cancelled events are hidden.
- **Jobs:** admins publish and close job opportunities. Each needs an application link, a contact email, or both. Members apply on the external page or by email; there are no in-app applications.
- **Safety:** links must be http(s). All write endpoints check roles on the server.
- **Mentor recommendations** show a ranked label (Best match, Strong match, Good match) instead of a percentage. The ranking is relative to the recommendations shown.
- **Matching index:** mentor profiles are now added to the vector index when a mentor registers, completes Clerk onboarding, creates a profile or edits it. Previously only `seed_mentors.py` indexed mentors.
