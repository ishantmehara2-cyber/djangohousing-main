# Architecture: Housing.clone

Housing.clone follows the standard Django MVT (Model-View-Template) architectural pattern with modular app separation.

## Django Apps
- **`apps.accounts`**: Custom User model, authentication, role-based permissions, and user dashboard views.
- **`apps.properties`**: Property catalog, filtering, search engine, media management, and property detail views.
- **`apps.locations`**: States, cities, localities, and sub-localities hierarchy.
- **`apps.engagements`**: Favourites, enquiries, visits, saved searches, recently viewed, and smart discover recommendations.
- **`apps.billing`**: Packages, subscriptions, payment transactions, invoices, and property promotions.
- **`apps.moderation`**: Admin moderation queue, property verification, flagged reports, and audit logs.
- **`apps.core`**: Homepage, legal pages, help centre, support ticket system, sitemap, and robots.txt.
- **`apps.projects`**: Developer organizations and RERA-registered real estate projects.
- **`apps.brokers`**: Verified broker and agent directory.
