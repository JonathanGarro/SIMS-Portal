# Models

## National Societies

The national society table contains columns for the national society's name, the country name, and the IFRC GO platform unique ID for that country. This data is relatively static and therefore does not have any automated updated processes. However, it is recommended that you periodically run API requests to the `country` table on the platform, in case national society names change, new countries form, or GO updates the unique identifiers. The `additional_py_scripts` folder has a file called `GO_API_countries` that will call the GO Platform, loop through the countries table, and generate a list of those values.