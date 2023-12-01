# SIMS Portal Release Notes

![DC Metro Map Isolated](https://github.com/JonathanGarro/sims-portal-releases/assets/8890661/88a441fe-47b6-4874-90e6-83d3a64f0341)

- Patch (0.0.X) releases are minor bug fixes and code enhancements. 
- Minor (0.X.0) and major (X.0.0) releases introduce new features and follow the Washington DC Metro system's station names on the Red Line, starting at Shady Grove.

# 1.7.5 (Friendship Heights) - 2023-12-01

## New Features

- **Bulk Slack Avatar Update**: A new function has been added to the manual refresh page within the admin portal to loop over all members that have the default.png avatar and update their photo with the one they have associated with their Slack account.

# 1.7.4 (Friendship Heights) - 2023-11-30

## Changes

- **Add Guidance for SIMS Remote Coordinator Product Approvals**: Products awaiting approval for public posting now include a link for the SIMS Remote Coordinator to learn how to evaluate what is and isn't appropriate to share. 

## Fixes

- **Fix URL Scheme for Link to Learning Site for Products**: The migration of the SIMS learning site required swapping links from IDs that were integers to URLs, which meant changing the datatype of the column in the database and fixing how the page rendered the link.
- **Fix Broken Links on Role Profile Pages**: Links to the category pages on SIMS learning site were fixed on role profile pages.

# 1.7.3 (Friendship Heights) - 2023-11-20

## Changes

- **Documentation Links Open New Tabs**: Links to documentation on learn-sims.org now open as new tabs in the user's browser.
- **Update Stroke Width on Map**: The response history map on the about page has been updated to be thicker in order to be more visible on smaller screens.

## Fixes

- **Tooltip Link Fixes**: Tooltips with links to the new learn-sims.org site (which was moved from a separate host to the same AWS account as the Portal) have been updated.

# 1.7.2 (Friendship Heights) - 2023-11-07

## Changes

- **Registration Page Language**: Tweaked guidance language on the new user registration page.
- **Language and Skill Picker**: The profile edit page now utilizes checkboxes instead of plain text multi-selects for skills and languages.

# 1.7.1 (Friendship Heights) - 2023-10-31

## Changes

- **Member Directory Navigation**: The navigation for the active and inactive member directory has been updated.
- **Separate Support Profiles Card**: The "Support Profiles" information on member profiles has been moved to a separate card which only appears if the user has any assigned to them.
- **Dashboard Layout**: Minor enhancements to the map.

# 1.7.0 (Friendship Heights) - 2023-10-27

## New Features

- **National Society View**: Data can now be viewed by national society through dedicated pages for each society that has SIMS members. Access these pages through the navbar dropdown when logged in. These views show associated members and their domain specializations in order to centralize information for register managers.

## Changes

- **Documentation Styling**: Updated the styling to make the documentation table easier to read.
- **Portfolio Preview Styling**: Added border to products to improve visibility of products with a white background.

## Fixes

- **Missing Documentation Type on Form**: The "Web Visualization" option was previously missing from the new documentation form.

# 1.6.0 (Bethesda) - 2023-10-10

## Changes

### Learning and Reference Resources

- **Resource Index**: A new section that allows authors to post the link and description of their guide directly to the new resources page in order to further integrate the learn-sims.org site with the SIMS Portal. 

# 1.5.3 (Medical Center) - 2023-10-06

## Fixes

- **Broken Emergency Page Portfolio**: A jinja loop wasn't properly closed, leading to errors on the emergency page's "View More" link for the full list of approved products.

# 1.5.2 (Medical Center) - 2023-10-02

## Changes

- **Caching Static Images**: Most images are hosted on AWS S3, but for static files like icons and logos, a new route has been built to handle caching those images in order to improve site performance.
- **Profile Page Styling Tweaks**: The member status indicator has been refined.
- **SIMS Co Editing of Assignments**: The assignment page now utilizes the `check_sims_co` utility to validate that the user viewing the assignment is a SIMS Remote Coordinator for that particular emergency. If `True`, the user has access to assignment editing. 

## Fixes

- **Hide Closeout Button**: Removed "Closeout Emergency" button on emergency records that are no longer active in order to avoid re-pinging members with request to submit learning records.

# 1.5.1 (Medical Center) - 2023-09-24

## New Features

### Navigation

- **New Navbar**: To simplify the navigation panel, the top bar links have been swapped out for icons. This is part of a larger effort to make room for some additional features on the development roadmap.

### User Profiles

- **Member Status**: Profiles now display the user's status in the SIMS network—`Active`, `Inactive`, `Pending`, and `Other`.

## Changes

- **Dashboard Map Styling**: Darker borders to increase visibility on certain screens.

## Fixes

- **Portal Admin Page**: The Portal Admin listing page was broken due to a SQL error as part of the SQLite to PostgreSQL transition.
- **Emergency Page Tabs**: Certain tabs on the emergency page were displaying information incorrectly due to an extra closing `</div>` tag.

# 1.5.0 (Medical Center) - 2023-09-22

## New Features

### User Profiles

- **Private Profiles**: Based on feedback about data privacy, users can now mark their profile as private. This prevents their profile from appearing on the public-facing side of the site on the Members page, and adds their profile to a `robots.txt` file to prevent search engine indexing.
- **Bulk Slack Photo Import**: Admins now have access to a method for automatically updating all users' profiles that have not had a custom image associated with their Slack profile photo.

### Emergencies

- **Availability Details**: A table now shows how people have reported their availability. 

# 1.4.9 (Grosvenor-Strathmore) - 2023-09-14

## Fixes

- **Surge Alerter Fix**: The Geneva Surge team has been importing old surge alerts into the RRMS database as part of a historical data migration, and these don't follow the same structure that the import utility in the Portal was designed against. I have adjusted the script with try/except blocks to avoid errors.

# 1.4.8 (Grosvenor-Strathmore) - 2023-08-07

## New Features

### Role Profile Pages

- **Linkage with Learn-SIMS Site**: Role profile pages now include a link to the learning hub for that specific role profile.

## Changes

- **Active/Inactive Member Toggle**: The toggle to switch between active and inactive members has gotten a cleaner styling.
- **Tweaks to Landing Page**: Minor adjustments to the index page's layout and language.

## Fixes

- **Sort Order of SIMS Co Table**: The remote coordinators assigned to an emergency now appear in chronological order.
- **Sort Order of Emergency Types on New Emergency Page**: The dropdown now lists emergencies in alphabetical order.

# 1.4.7 (Grosvenor-Strathmore) - 2023-08-05

## Fixes 

- **Fix Learning Data Error**: The learning visualization added as part of 1.4.6 created a fatal error when viewing closed emergencies that had no learning data associated. 

# 1.4.6 (Grosvenor-Strathmore) - 2023-08-04

## Changes

- **d3 Learning Visualization**: The learning visualization which previously used chart.js has been replaced with a d3 visualization. This graph still needs additional work to improve its utility, including mouseover events. These will changes will be added to a future release.
- **Additional Cron Runs**: The frequency of the cron job that looks for new IM-related surge alerts has been increased following a successful beta period. 

## Fixes

- **Cleaner JS Imports**: The `layout.html` that handles the bulk of templates' JS imports has been cleaned up address a number of errors that were previously appearing the console. These mostly related to either outdated versions or trying to load functions that were not present on certain pages. These have been addressed with `if request.path ==` to only load when needed.

# 1.4.5 (Grosvenor-Strathmore) - 2023-07-31

## New Features

### Learning and Reference Resources

- **Post Operational Slack Alerts**: When an administrator closes out an emergency in the system, it sends a Slack message to each user listed as a Remote IM Supporter with a link to their learning survey. 

# 1.4.4 (Grosvenor-Strathmore) - 2023-07-30

## New Features

### API

- **Emergency Table Queries**: The API now accepts queries of the `emergencies` table, and accepts the following optional parameters: `status`, `emergency_id`, `iso3`. It adds a calculated column that shows the total number of assignments. See API documentation for more information.

## Fixes

- **Validation on Edited Email Address**: There was no form validation message shown to the user when trying to update their account with an already-registered email address. The system will now give clear feedback when a conflict occurs.

# 1.4.3 (Grosvenor-Strathmore) - 2023-07-28

## Changes

- **Pagination on Public Portfolio**: To save server resources, pagination has been added to the public portfolio for both filtered and unfiltered views.
- **API Documentation**: The footer now links to a dedicated API documentation page where users can test out queries to the database.

## Fixes

- **Correct Counting of Operations Supported**: The "operations supported" section of the member profile page was double counting when users supported the same operation in multiple capacities (e.g. both as a remote supporter and as a SIMS Remote Coordinator).
- **Correct Counting of Members Supporting on Story View**: Stories for emergencies were also double counting members that filled multiple roles.

# 1.4.2 (Grosvenor-Strathmore) - 2023-07-26

## New Features

### API

- **User Table Queries**: Query the `user` table to return results about our registered members. Accepts optional argument of users' statuses.
- **Portfolio Table Queries**: Query the approved products associated with a given emergency. Accepts required argument of the GO emergency's ID. 

# 1.4.1 (Grosvenor-Strathmore) - 2023-07-25

## New Features

### User Profiles

- **Inactive Member Listing**: The members page on the public section of the site now allows viewers to toggle between active and inactive members. The pagination buttons have also received new styling.

## Changes

- **Data Readiness Link**: The site footer has been updated to include a link to the [Data Readiness Toolkit](https://preparecenter.org/toolkit/data-readiness-toolkit/).
- **Redesigned Support Profile Pages**: The support profile pages have been cleaned up with a simpler navigation structure and new iconography. 

## Fixes

- **Profile Assignment Data Model Upgrade**: The system previously allowed multiple rows per profile, per member in the `users_profiles` lookup table. For example, if a member was assigned web viz tier 3, then later assigned web viz tier 4, the original record would be retained and the front end would filter the `max()` tier. This caused problems when admins tried to delete old records through the admin portal. The new route deletes existing records for the user in that profile type before assigning the new one in order to maintain a 1-1 relationship of users' profiles and tiers.
- **Fix PSQL Conditionals for 403 Pages**: The conversion from SQLite to PostgreSQL for the backend broke some SQLAlchemy queries because of how booleans are handled (`True` instead of `1`). All instances of the 403 error page redirect now use the correct syntax.

# 1.4.0 (Grosvenor-Strathmore) - 2023-07-24

## New Features

### User Profiles

- **Slack Photo Integration**: Members can now optionally use the photo from their SIMS Slack account as their profile photo. The new feature uses the assigned Slack ID on the user's profile to ping the API and pull down the associated photo.
- **Improved User Profile Management**: The user profile controls—including updating personal information, saving work location, resetting password, downloading Slack photo, and deleting account—have been moved to a sliding Bootstrap pane.

# 1.3.1 (North Bethesda) - 2023-07-19

## Fixes

- **Resource Page Link Correction**: Moved the documentation link destination for product approval status on portfolio pages to the learn-sims.org site.
- **Story Image on Index**: Fixed a 1.3.0-related change around moving story images to S3 broke the image lookup on the index page.

# 1.3.0 (North Bethesda) - 2023-07-18

## New Features

### Stories

- **Header Images Save to S3**: This release moves story header images into S3 in order to maintain the data when deploying updated Docker containers to AWS.

# 1.2.5 (Twinbrook) - 2023-07-17

## New Features

### Configuration

- **Gunicorn Integration**: The Portal now uses green unicorn ("gunicorn") as the Web Server Gateway Interface (WSGI) in production.

## Changes

- **Better Date Formatting**: Utilized same method from 1.2.4 release on the internal portfolio table.
- **Additional Datatable Controls**: Added new search field to full portfolio view for logged-in users.
- **Improved CSS on Stories**: The special markdown classes have been updated to improve the visual styling on story pages.

## Fixes

- **Member Table Filtering**: The member table for logged-in users didn't show members that had no assignments, due to a SQL join error. This has been fixed with new left joins to feed that table.

# 1.2.4 (Twinbrook) - 2023-07-12

## Changes

- **Assignment Quick Access**: The quick access button released with **1.2.3** has been updated with improved visual styling.
- **Better Date Formatting**: Dates on the dashboard and emergency page now use an easier-to-read format of month day, year (e.g. "July 12, 2023")

# 1.2.3 (Twinbrook) - 2023-07-10

## New Features

### User Profiles

- **Delete Skills**: Users can now delete skills they've assigned themselves from their profile edit page. 

### Emergencies

- **Assignment Quick Access**: When viewing an emergency for which the user has an active remote support assignment, an alert box in the left pane appears, offering quick access to the assignment record.

### Changes

- **Paginated Member Cards**: To reduce load times on members page on public view, the cards are now be limited to four rows with 'next' and 'previous' buttons conditionally appearing at the bottom.

## Fixes

- **Logging Issues Related to Alembic**: After implementing `flask-migrate` to handle database model changes, it broke logging to our Logtail instance. This was related to an [identified issue](https://github.com/miguelgrinberg/Flask-Migrate/issues/227) in `flask_migrate.upgrade()` during initialization.

# 1.2.2 (Twinbrook) - 2023-07-05

## New Features

### Availability

- **Better Data Management and Visualization**: Building off the availability reporting feature introduced in 1.2.0, users can now more easily make changes to their previous reports. Past reports are overwritten rather than appended. The availability tab on the emergency page now summarizes the data for the week in a bar chart.

## Changes

- **Separated Support Tables**: The emergency page now splits up supporters into three distinct tables: Remote Coordinators, Remote Supporters, and deployed IM delegates, the latter being a collapsed table that can be expanded.
- **PEP-8 Compliant Imports**: As part of a larger effort to clean up the codebase, the imports on various routes have been reorganized to make them easier to read.

## Fixes

- **DataTable Error in Admin View**: Fixed an error thrown by a conflicting javascript function when viewing the assigned profiles table.

# 1.2.1 (Twinbrook) - 2023-07-01

## Changes

- **Verify Slack ID on Approval**: In order to validate that users are not spoofing the registration process, a link to their Slack DM has been added to the new user approval route for Admins that asks them to check the Slack ID with a quick link.

## Fixes

- **D3.js Map**: Fix the timing on the map markers so they stay on until the horizon and reappear correctly.
- **Broken Slack DM Link**: The URL pattern for direct linking to a user's Slack DM was previously not properly configured.

# 1.2.0 (Twinbrook) - 2023-06-30

## New Features

### Availability

- **Weekly Availability**: Users can now report their availability for providing remote support to operations. When users open the emergency's page, there is an option to provide their availability for the current week. As the next week approaches (starting Thursdays), they can also report for the upcoming week. A calendar provides a visual summary of the days they have selected. 
- **Cron Job Trigger**: A function has been added that runs on Monday morning which loops over active emergencies and sends a Slack message to the relevant disaster channel with a direct link to the reporting form. This is currently toggled off, pending socialization with the SIMS network.

## Changes

- **Slack API Caching**: Added caching to the Slack API calls that get the list of users and IDs. There is a rate limit of one call per minute, which caused an error if multiple people were registering at once. The cache now stores the results for two minutes to avoid the limit.
- **Hide Map on Landing Page**: Users reported that some mobile phones would freeze when viewing the index page as a result of the D3.js animation. This element is now hidden when viewing the site on smaller screens.
- **Emergency Page Navigation**: The layout and available actions on emergency pages have been redesigned. Only administrators can assign the first SIMS Remote Coordinator (subsequent rounds can be assigned by either administrators or existing/previous SIMS Remote Coordinators). Regular users cannot assign themselves to emergencies any more—Coordinators must do this.

# 1.1.1 (Rockville) - 2023-06-15

## Changes

- **Navbar Font Sizing**: The title and nav menu links have been shrunk to ensure text doesn't get cutoff on mobile devices.

## Fixes

- **Forgot Password Error**: A bug that would give the user an error message when using the "Forgot Password" feature, which was related to a logging issue, has been fixed.

# 1.1.0 (Rockville) - 2023-06-03

## New Features

### Portfolios

- **KM Link**: Added linkage for portfolio view back to the relevant tutorial or guide in learn-sims.org. When `km_article_id` is not null, a button will appear that links to the guide. Updating this field must be done in the admin area by editing the product's information in the "Portfolio" tab.

## Fixes

- **Member Count**: Emergency pages now count each person only once, whereas it used to count each assignment (meaning if someone served as a remote coordinator then as a remote supporter, they were getting double counted).
- **Root URL**: With migration from CloudFront staging domain to rcrcsims.org, update the `ROOT_URL` in the `config.py` file to support external links.

# 1.0.3 (Shady Grove) - 2023-05-29

## Fixes

- **New Assignment Form**: Removed "FACT/CAP" from assignment type.
- **Limited Edition Image Path**: Fix for limited edition paths stored in S3.

# 1.0.2 (Shady Grove) - 2023-05-25

## Changes

- **All Emergencies Search Removed**: Remove broken link to old custom search page.
- **Manual Refresh of User Locations**: Temporary stopgap solution to allow administrators to regenerate the CSV that feeds the landing page's red dots that represent the locations of SIMS members around the world.

# 1.0.1 (Shady Grove) - 2023-05-23

## New Features

### Other

- **Release Tracker on GitHub**: A new page for tracking release features. We'll be following the Red Line stations from the Washington, DC Metro system for major new releases.

## Changes

- **Release Tracker Link**: The new release tracker has been added to the `layout.html` file.
- **Footer Redesign**: A new layout was added to include additional links and remove generic SIMS blurb.

# 1.0 (Shady Grove) - 2023-05-20

## New Features

### User Profiles

- **Registration**: SIMS members can sign up using their Slack ID in the SIMS Slack account to verify. Once registered, they are placed into a queue for an administrator to approve. This helps triage who needs to be onboarded for the portal, and ensure only qualified members have full access. 
- **Support History**: Users can maintain a running record of the emergencies to which they have provided support.
- **Bio**: Users can share information about themselves in markdown format. 
- **Portfolio Highlights**: Users can post their finished products and supporting design assets to the Portal for each emergency they support, and have them appear on their profile.
- **Support Profiles**: SIMS Administrators can assign members one or more support profiles, which lets others know what types of products they can create and services they can provide. Each profile has an associated tier, with guidance around who qualifies for what tier.
- **Skills and Languages**: Users can tag the relevant technical skills they possess across a variety of areas, and tag the languages they speak in order to help others find the right person for specific questions.
- **Badges**: Achievement and recognition badges that are given to users appear on their profiles, along with the justification for getting it.
- **Location**: Users can take advantage of the Google Maps integration to search for a location where they work from, in order to help visualize our reach and organize our support across time zones.

### Emergencies

- **Emergency Records**: Each SIMS activation gets its own emergency record, where our collective response is maintained. 
- **Activation Details**: Information can be entered about the emergency itself, as well as the process involved with activating SIMS to support it.
- **Trello Integration**: Each emergency can parse the tagged Trello board to extract open (unassigned) Trello tasks.
- **Learning**: Individual remote supporters and SIMS Remote Coordinators can provide feedback and learning for each response. Remote supporters are given the option of answering a brief survey at the end of their assignment, and Remote Coordinators can provide real-time feedback in a longer-form mechanism. 
- **Badge Assignment**: SIMS Remote Coordinators can assign remote supporters specific badges as they recognize stellar work.
- **Assignment Table and Gantt**: A table summarizes each remote supporter's involvement, and can be visualized with a D3-based Gantt chart.
- **Response Products**: As users post products, if they tag them as "Public", they get placed into a queue for the SIMS Remote Coordinator to review. If approved—meaning it is appropriate to share externally—it will appear for site visitors without having to log in. Products are uploaded by the Portal to Dropbox, where other members can access the underlying assets to reuse or remix them.
- **Response Tools Linkages**: The Portal connects with Slack, Dropbox, and Trello to ensure visitors can find the most important products, assets, and communication channels. 
- **Response Stories**: SIMS Remote Coordinators can draft markdown-friendly blog posts that summarize our response, document key learnings and achievements, and automatically synthesize our statistics. 

### Assignments

- **Tagging to Emergencies**: Each remote supporter's involvement in an emergency is saved as an assignment (only one assignment is necessary even if the person works on multiple products with gaps in between). 
- **Basic Information**: Assignments store basic info about what the person was generally tasked with doing, when they started and ended their support (as estimates), and serves as the vehicle for saving products that the remote supporter created or supported on for that particular emergency.
- **Availability**: For larger-scale, high-volume emergencies, the availability feature can be utilized. Remote supporters can navigate to their assignment and report which days they are available to support. This can help with organizing coverage during intense periods of field requests.

### Public Marketing

- **About Page**: The about page automatically updates with key metrics, including the full list of our activations, a count of active members, and a D3.js map that displays our response history.
- **Profile Types**: Dedicated pages are linked to from the about page that show the basics about each of our remote support profiles, as well as granular descriptions of how each tier (from 1 to 4) differ.
- **Public Portfolio**: Products that are requested to be public and approved by SIMS Remote Coordinators are visible in the portfolio, and filterable by type. 
- **Member Directory**: A full list of active members is available to site visitors, along with individual profiles for each member. These profiles closely match the profile one sees when logged in, but with only publicly-visible portfolio items visible.

### Admin Controls

- **Profile Management**: Admins can assign one ore more support profiles to members.
- **Badge Assignment**: While SIMS Remote Coordinators will typically be the person assigning badges as part of a given response, admins can also assign badges. These include "Special Edition" badges that SIMS Remote Coordinators do not have access to.
- **Member Approvals**: When new users sign up, their accounts are tagged as conditional until an admin approves it.
- **Open Reviews**: A listing of all the SIMS Remote Coordinators' learning records. Admins can see the full list and approve or reject the information in order to process it into standard operating procedures or other change management tools. 
- **Skill Picklist Controls**: Admins can add to the list of skills we track on member profiles.
- **New Badge Uploads**: Admins can create new badges. When created, the badge automatically populates the badges index page and calculates how common it is among SIMS members.

### Learning and Reference Resources

- **Organization by Support Profile**: The resources page organizes our knowledge management articles and guides by our primary support profiles. There are also hubs for standard operating procedures, style guides, and SIMS Portal documentation for admins.
- **learn-sims.org**: In order to make our guide-drafting process open and collaborative, the guides are hosted on a separate site running WordPress. Users can be added to that site and author their own guides and tutorials. 

### Other

- **GO Surge Alerts**: The Portal runs a cron job that downloads the latest surge alerts from the GO API and summarizes them on the dashboard for logged-in members. New alerts trigger a Slack message that gets posted to the Availability channel on the SIMS account, along with basic information about the deployment request.
- **Data Overview**: A few basic visualizations are embedded in the dashboard, to support simple reporting on key metrics.