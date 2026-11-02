# Landing page hero image

The landing hero uses a Kenya Airways aircraft photograph supplied by the project owner. It is bundled at `frontend/src/assets/brand/hero-aircraft.webp` (converted from the original 1902x562 PNG to WebP) and shown at the top of the hero, fading into the dark hero background so the aircraft is never cropped.

Before publishing, confirm that Kenya Airways has approved this photograph for the public AlumniConnect site.

## Replacing the image without a code change

1. Place an approved photo in `frontend/public/images/` (for example, `alumni-community-hero.webp`).
2. Add `VITE_LANDING_HERO_IMAGE=/images/alumni-community-hero.webp` to the frontend environment used for the build.
3. Rebuild and confirm the image permission/license and descriptive alt text before publishing.

The override replaces the bundled aircraft photo. A wide image (about 3.4:1, like the supplied one) works best, because the hero layout reserves a band of that proportion at the top and starts the headline below it.

The page does not use an external image URL.
