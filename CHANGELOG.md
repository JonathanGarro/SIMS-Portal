# SIMS Portal Release Notes

![DC Metro Map Isolated](https://github.com/JonathanGarro/sims-portal-releases/assets/8890661/88a441fe-47b6-4874-90e6-83d3a64f0341)

- Patch (0.0.X) releases are minor bug fixes and code enhancements. 
- Minor (0.X.0) and major (X.0.0) releases introduce new features and follow the Washington DC Metro system's station names on the Red Line, starting at Shady Grove.

# 1.10.2 (Cleveland Park) - 2024-05-21

## New Features

- **SIMS GitHub Organization**: After Trello introduced some changes to the free tier, SIMS was forced to explore other options. As we pilot using GitHub teams as a way to manage tasks, we needed a way to quickly add people to the organization in GitHub. Now, when users add or change their GitHub username on their profile, it will automatically send them an invite to the SIMS org.

# 1.10.1 (Cleveland Park) - 2024-05-16

## New Features

- **Slack Channel Generator**: When a user creates a new emergency, the system will now automatically generate a new Slack channel for the activation. 

# 1.10.0 (Cleveland Park) - 2024-05-13

## New Features

- **Overhauled Dashboard**: The dashboard users see when they first log into the system has been rebuilt. The map and widgets have been updated and the queries that power them have been re-written for better performance. The IM surge alerts now only show open positions, and the tables summarizing currently activated coordinators has been reformatted. 

# 1.9.9 (Van Ness) - 2024-05-09

## New Features

- **Pagination for Acronyms**: The acronym index now has pagination to limit the load time. 
- **Single Page Search for Acronyms**: Rather than have to return to the acronym landing page to adjust a search, users can now run new searches directly from the results page.

## Fixes

- **NULL Values for Edited Acronyms**: Fix an issue where updating an acronym would insert blanks instead of NULLs, which was causing issues on the template.
- **Adjust Acronym Edit Submit Button**: The Bootstrap class was incorrectly limiting the size of the button and cutting off the text.

# 1.9.8 (Van Ness) - 2024-05-07

## New Features

- **More Robust Acronym Search**: As the list of acronyms grows vertically (more records) and horizontally (additional languages and other metadata), it has become unwieldy to search for what you need. The new acronym index landing page offers more granular controls for users.

# 1.9.7 (Van Ness) - 2024-05-06

## Fixes

- **Spacing Fixes for Firefox**: Fixed spacing of elements in various templates that weren't behaving as expected in Firefox browsers.
- **Acronym Validation Fix**: When migrating the db, a validation got incorrectly created for the logged-in route. 
- **Enforce Null Values on Acronym Records**: When posting a new acronym, unused fields (e.g. other languages) were being posted with blanks instead of `NULL`, so a simple conditional has been added.
- **Remove Length Conditional on Acronym Template**: Related to fix above, the jinja used to display the values from the acronyms in other languages has been adjusted to handle `NULL` values.

# 1.9.6 (Van Ness) - 2024-03-19

## Fixes

- **Surge Alert Downloader Fix**: In response to some errors parsing surge alerts from the GO API, I needed to set Molnix tag values to None by default in case the surge desk doesn't correctly fill these in.

# 1.9.5 (Van Ness) - 2024-03-14

## New Features

- **Dynamic Regional Surge Email Address**: The regional surge email address is now displayed in alert messages sent to the Availability channel in Slack. For example, Europe regional alerts will now be tagged with surge.europe@ifrc.org.

## Fixes

- **Logging Messages**: Several log message formatters have been corrected. 

# 1.9.4 (Van Ness) - 2024-03-11

## New Features

- **Activity Logs**: I recently moved logging out of Logtail and created a custom solution with a dedicated table in the database. Access to those logs required connecting to the database directly using database management software. This release makes those logs available in the front end for all administrators.
- **Regional IM Lead Cards**: The dashboard now shows the five active Regional IM Leads. 

## Fixes

-**Alphabetize Compact Acronyms List**: The compact version of the acronym table is now ordered correctly.

# 1.9.3 (Van Ness) - 2024-03-08

## New Features

- **Tag Regional IM Focal Point on Availability Messages**: The script that grabs new surge alerts from the GO API and sends them to the Availability channel in the SIMS Slack now tags the Regional IM Focal point, ensuring that conversations about the alert include them. Adding this feature also meant creating another Admin Portal page with the ability to manually assign which member is the current IM focal point for each region.

## Fixes

- **Fixed Link to Admin Pages**: With the upgraded admin portal, a few links for Slack alerts and banners needed to be updated.

# 1.9.2 (Van Ness) - 2024-03-02

## Changes

- **reCAPTCHA on Public Acronym Form**: Following an attempted SQL-injection attack against the database, I've implemented a reCAPTCHA check on the public version of the acronym submission form and added additional validations. Is it weird that I'm a bit flattered that a hacker found our database worthy of being hacked?

# 1.9.1 (Van Ness) - 2024-02-29

## Fixes

- **Acronym Export**: This release contains a minor patch intended to fix how the CSV export, which was previously mapping fields incorrectly and generating errors.

# 1.9.0 (Van Ness) - 2024-02-28

## New Features

- **Overhauled Admin Portal**: With additional controls for admins, the page where those utilities were managed was getting cluttered. The new design offers better navigation, and routing now allows for better redirects in Flask after completing a function.
- **Richer Acronym Management and Views**: A more compact view of the acronym list has been added. On the regular view, a popup window is now available that displays the acronym in various languages (when available) for faster at-a-glance reviews. Admins and the person that created the acronym can also edit the records.

# 1.8.3 (Tenleytown) - 2024-02-26

## Changes

- **Acronym Submission Logic**: Non-logged in users may now submit acronyms anonymously. Their submissions are put into a review queue before posting, while SIMS members that log into the system before submitting will have their submissions directly saved.
- **Acronym Compact View**: A separate view for seeing all acronyms on a single page has been created for those who want to skim through all available entries.

# 1.8.2 (Tenleytown) - 2024-02-23

## New Features

- **Slack Availability Channel Surge Alerter**: The script that downloads surge alert data, parses IM-related alerts, and pings the Availability channel in the SIMS Slack account has been rebuilt to take advantage of improvements made to the GO API last year. The alert messages to that channel now include rotation number, language requirements, a link to the alert in Molnix, and more. It handles exceptions better and includes new logging to better track when the Surge Desk puts data into the system that isn't properly structured against the data model. 

# 1.8.1 (Tenleytown) - 2024-02-21

## New Features

- **New Acronym Alerts**: A Slack alert is now sent to the SIMS Portal API channel in the SIMS Slack to let administrators know that there is a new item in the review queue.

## Fixes

- **Broken Links on Resources Page**: Links to the learn-sims knowledge management portal have been fixed. (Thanks Natalie!)
- **Fixed Link Builder on Acronym Table**: The link generator for external resources was not being constructed correctly, but has been fixed.

# 1.8.0 (Tenleytown) - 2024-02-20

## New Features

- **Custom Logging**: After trialing BetterStack, I decided to implement a customized logging solution that stores logs in a dedicated table in the SIMS Portal database. This release includes the first pass at triggers for common actions like user logins and file uploads.
- **Acronym Index**: A new collaborative index allows users to post acronyms along with their definitions, supporting information, and relevant links. The system supports English, French, and Spanish. Arabic to be considered in the future.

# 1.7.7 (Friendship Heights) - 2024-01-19

## New Features

- **Alert Remote Coordinator on Public Product Upload**: When a remote supporter uploads a product and marks it as "Public", the active (or most recently active) SIMS Remote Coordinator gets an alert in Slack with a link to the review.

## Changes

- **Updated Language on Profile Edit Form**: With switch to checkboxes for language and skill picker, the language on this page needed to be changed.

## Fixes

- **Adjust Emergency Page Spacing for Mobile**: As part of broader effort to improve experience on mobile, some elements have had spacing and resizing adjusted on the Emergency page.
- **New Icons in Navigation Ribbon**: The icons used for the ribbon when logged in were fuzzy on larger screens, so the PNGs have been updated with SVGs. 
- **Fix Date Format on SIMS Co Gantt Chart**: A pesky bug that was preventing dates from being displayed correctly when hovering over bars in the Gantt chart has been fixed.

# 1.7.6 (Friendship Heights) - 2023-12-04

## Fixes

- **Override Form Submit Text on Availability**: The submit button on the availability reporting form was showing inconsistent label values, so these have new `value=` tags.
- **Higher Resolution Icons in Ribbon**: The navigation ribbon for logged-in users now use SVGs in order to avoid pixelation.

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