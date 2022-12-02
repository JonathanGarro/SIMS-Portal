<img width="1705" alt="Screen Shot 2022-11-03 at 10 56 00 AM@2x" src="https://user-images.githubusercontent.com/8890661/199755519-d4ad8109-8ec5-4c45-abef-1e2af86fef0d.png">


# SIMS-Portal-Neo

The Surge Information Management Support (SIMS) system is a global network of Information Management experts who support IFRC emergency response operations by providing a variety of services and products. We maintain a roster of specialists from around the world across several key areas of technical support, including GIS, data collection and management, data analysis and visualization, and much more.

The SIMS Portal is a site for external audiences to learn more about what SIMS does, and an internal area for members to organize their work, manage their profiles, and access resources. The portal has been built using the Flask framework, and manages the data inside an SQLite database file. 

## Features

### External Viewers
External users can access the landing page, which provides an overview of the SIMS network, as well as several tabs that provide a history of the network, an overview of our members with access to their external profiles, and a live-view into our portfolio of work (for products tagged as being externally-friendly). 

### Logged-In Members
Logged-in members can access a dashboard that provides an overview of active operations and members currently supporting them. They can view and update their own profiles, including providing information on the languages they speak and the skills they possess. Profiles also show their achievement badges, each of which can be clicked on to see more information about the badge as well as how common it is. 

Emergencies that SIMS is currently responding to or has responded to in the past are stored as individual records. Each emergency can have one or more assignments associated with it, and each assignment is filled by a single SIMS member. Assignments are where members can post the work they completed as part of that response, and those products can be viewed in the emergency page, the user's profile page, and (if marked as external) on the publicly-accessible portfolio page.
