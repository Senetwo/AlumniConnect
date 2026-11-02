# Backend automated test record

Date: 2026-11-02 | Commit: e87ad93 | Runner: pytest (in-memory SQLite)

Total: 85 | Passed: 85 | Failed: 0 | Skipped: 0

| Module | Test | Expected behaviour | Actual | Corrective action |
|---|---|---|---|---|
| test_admin_api | `test_admin_cannot_demote_self` | Admin cannot demote self | passed | - |
| test_admin_api | `test_admin_dashboard_uses_real_counts_and_marks_untracked_metrics` | Admin dashboard uses real counts and marks untracked metrics | passed | - |
| test_admin_api | `test_admin_user_management_is_role_protected_and_audited` | Admin user management is role protected and audited | passed | - |
| test_admin_bootstrap | `test_bootstrap_can_only_be_used_once` | Bootstrap can only be used once | passed | - |
| test_admin_bootstrap | `test_bootstrap_elevates_only_allowlisted_existing_account` | Bootstrap elevates only allowlisted existing account | passed | - |
| test_admin_bootstrap | `test_bootstrap_refuses_unlisted_identity` | Bootstrap refuses unlisted identity | passed | - |
| test_auth | `test_admin_self_registration_is_rejected` | Admin self registration is rejected | passed | - |
| test_auth | `test_authenticated_user_can_be_retrieved` | Authenticated user can be retrieved | passed | - |
| test_auth | `test_duplicate_email_registration_is_rejected` | Duplicate email registration is rejected | passed | - |
| test_auth | `test_invalid_login_is_rejected` | Invalid login is rejected | passed | - |
| test_auth | `test_mentee_cannot_access_admin_profiles_endpoint` | Mentee cannot access admin profiles endpoint | passed | - |
| test_auth | `test_register_mentee` | Register mentee | passed | - |
| test_auth | `test_register_mentor` | Register mentor | passed | - |
| test_auth | `test_registration_creates_linked_user_and_profile` | Registration creates linked user and profile | passed | - |
| test_auth | `test_unauthenticated_user_cannot_access_profiles` | Unauthenticated user cannot access profiles | passed | - |
| test_auth | `test_valid_login_returns_access_token` | Valid login returns access token | passed | - |
| test_chat | `test_accepted_mentorship_appears_as_one_named_chat` | Accepted mentorship appears as one named chat | passed | - |
| test_chat | `test_messages_persist_between_authorized_participants` | Messages persist between authorized participants | passed | - |
| test_chat | `test_pending_mentorship_does_not_create_a_chat` | Pending mentorship does not create a chat | passed | - |
| test_chat | `test_unrelated_user_cannot_read_mentorship_messages` | Unrelated user cannot read mentorship messages | passed | - |
| test_clerk_auth | `test_clerk_request_returns_verified_subject` | Clerk request returns verified subject | passed | - |
| test_clerk_auth | `test_invalid_or_expired_clerk_token_is_rejected` | Invalid or expired clerk token is rejected | passed | - |
| test_clerk_auth | `test_missing_clerk_configuration_fails_closed` | Missing clerk configuration fails closed | passed | - |
| test_clerk_auth | `test_signed_out_clerk_state_is_rejected` | Signed out clerk state is rejected | passed | - |
| test_community_feed | `test_blank_and_oversized_posts_are_rejected` | Blank and oversized posts are rejected | passed | - |
| test_community_feed | `test_blocked_members_do_not_see_each_others_posts` | Blocked members do not see each others posts | passed | - |
| test_community_feed | `test_cancelled_events_disappear_and_reject_rsvps` | Cancelled events disappear and reject rsvps | passed | - |
| test_community_feed | `test_closed_and_expired_jobs_are_hidden` | Closed and expired jobs are hidden | passed | - |
| test_community_feed | `test_daily_post_limit` | Daily post limit | passed | - |
| test_community_feed | `test_event_validation` | Event validation | passed | - |
| test_community_feed | `test_feed_requires_sign_in` | Feed requires sign in | passed | - |
| test_community_feed | `test_job_needs_a_way_to_apply_and_safe_links` | Job needs a way to apply and safe links | passed | - |
| test_community_feed | `test_like_is_idempotent_and_reversible` | Like is idempotent and reversible | passed | - |
| test_community_feed | `test_member_can_post_and_everyone_sees_it_newest_first` | Member can post and everyone sees it newest first | passed | - |
| test_community_feed | `test_members_rsvp_and_count_updates` | Members rsvp and count updates | passed | - |
| test_community_feed | `test_only_admins_create_events` | Only admins create events | passed | - |
| test_community_feed | `test_only_admins_publish_jobs_and_members_can_read_them` | Only admins publish jobs and members can read them | passed | - |
| test_community_feed | `test_only_author_or_admin_can_delete` | Only author or admin can delete | passed | - |
| test_community_feed | `test_past_events_are_not_listed` | Past events are not listed | passed | - |
| test_login_otp | `test_correct_code_issues_a_working_token_once` | Correct code issues a working token once | passed | - |
| test_login_otp | `test_email_is_matched_regardless_of_letter_case` | Email is matched regardless of letter case | passed | - |
| test_login_otp | `test_expired_code_is_rejected` | Expired code is rejected | passed | - |
| test_login_otp | `test_malformed_codes_are_rejected_before_any_lookup` | Malformed codes are rejected before any lookup | passed | - |
| test_login_otp | `test_password_login_asks_for_a_code_instead_of_issuing_a_token` | Password login asks for a code instead of issuing a token | passed | - |
| test_login_otp | `test_resend_has_a_cooldown_and_replaces_the_old_code` | Resend has a cooldown and replaces the old code | passed | - |
| test_login_otp | `test_step_can_be_switched_off_by_configuration` | Step can be switched off by configuration | passed | - |
| test_login_otp | `test_wrong_code_counts_down_and_locks_the_challenge` | Wrong code counts down and locks the challenge | passed | - |
| test_login_otp | `test_wrong_password_never_creates_a_challenge` | Wrong password never creates a challenge | passed | - |
| test_matching | `test_rank_matches_handles_empty_mentor_list` | Rank matches handles empty mentor list | passed | - |
| test_matching | `test_rank_matches_orders_by_similarity` | Rank matches orders by similarity | passed | - |
| test_matching | `test_rank_matches_returns_all_mentors` | Rank matches returns all mentors | passed | - |
| test_matching_api | `test_matching_by_id_only_allows_current_mentee` | Matching by id only allows current mentee | passed | - |
| test_matching_api | `test_matching_by_id_requires_authentication` | Matching by id requires authentication | passed | - |
| test_matching_api | `test_matching_me_rejects_admin_registration` | Matching me rejects admin registration | passed | - |
| test_matching_api | `test_matching_me_rejects_mentor` | Matching me rejects mentor | passed | - |
| test_matching_api | `test_matching_me_requires_authentication` | Matching me requires authentication | passed | - |
| test_matching_api | `test_matching_me_returns_ranked_mentor_recommendations` | Matching me returns ranked mentor recommendations | passed | - |
| test_matching_api | `test_mentor_profile_only_exposes_recommended_mentors` | Mentor profile only exposes recommended mentors | passed | - |
| test_matching_api | `test_mentor_profile_requires_authentication` | Mentor profile requires authentication | passed | - |
| test_mentor_index_sync | `test_index_failures_never_break_the_request` | Index failures never break the request | passed | - |
| test_mentor_index_sync | `test_mentees_and_suspended_mentors_are_removed_from_the_index` | Mentees and suspended mentors are removed from the index | passed | - |
| test_mentor_index_sync | `test_mentor_profiles_are_indexed` | Mentor profiles are indexed | passed | - |
| test_mentor_index_sync | `test_nothing_is_indexed_when_running_tests` | Nothing is indexed when running tests | passed | - |
| test_mentorship | `test_cannot_respond_to_non_pending_request` | Cannot respond to non pending request | passed | - |
| test_mentorship | `test_create_request_requires_authentication` | Create request requires authentication | passed | - |
| test_mentorship | `test_declined_request_can_be_submitted_again` | Declined request can be submitted again | passed | - |
| test_mentorship | `test_duplicate_active_request_is_rejected` | Duplicate active request is rejected | passed | - |
| test_mentorship | `test_invalid_mentor_is_rejected` | Invalid mentor is rejected | passed | - |
| test_mentorship | `test_mentee_can_request_mentorship` | Mentee can request mentorship | passed | - |
| test_mentorship | `test_mentee_cannot_respond_to_mentorship_request` | Mentee cannot respond to mentorship request | passed | - |
| test_mentorship | `test_mentee_cannot_view_incoming_requests` | Mentee cannot view incoming requests | passed | - |
| test_mentorship | `test_mentee_outgoing_requests_include_names` | Mentee outgoing requests include names | passed | - |
| test_mentorship | `test_mentor_can_accept_request` | Mentor can accept request | passed | - |
| test_mentorship | `test_mentor_can_decline_request` | Mentor can decline request | passed | - |
| test_mentorship | `test_mentor_can_view_incoming_requests` | Mentor can view incoming requests | passed | - |
| test_mentorship | `test_other_mentor_cannot_respond_to_request` | Other mentor cannot respond to request | passed | - |
| test_plus_alias_login | `test_clean_alias_signs_in_only_when_enabled` | Clean alias signs in only when enabled | passed | - |
| test_plus_alias_login | `test_display_and_mask_hide_the_owner_address` | Display and mask hide the owner address | passed | - |
| test_profiles_api | `test_get_my_profile` | Get my profile | passed | - |
| test_profiles_api | `test_get_my_profile_requires_authentication` | Get my profile requires authentication | passed | - |
| test_profiles_api | `test_update_my_profile` | Update my profile | passed | - |
| test_profiles_api | `test_update_my_profile_requires_authentication` | Update my profile requires authentication | passed | - |
| test_vector_store | `test_add_and_get_mentor` | Add and get mentor | passed | - |
| test_vector_store | `test_search_mentors_returns_similarity` | Search mentors returns similarity | passed | - |
| test_vector_store | `test_vector_store_count` | Vector store count | passed | - |
