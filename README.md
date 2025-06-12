# Pictures of a Thousand Words

## Description
This project contains a data pipeline that draws unformatted JSON objects from the MediaWiki API and formats them into a number of CSV and Excel files. These files will be used to create a [Tableau dashboard](https://public.tableau.com/app/profile/jasonwu00/viz/PicturesofaThousandWords/MainDashboard).

## Historical Context
For the better part of the last eight or so years I have been participating in writing and setting-building for personal entertainment reasons. A month ago, as part of an application for a position with The Data School, I decided to investigate the growth and development of a writing project that formed from this hobby over the last two years. The pipeline in this repository produced the files in the datasets folder that went into a Tableau dashboard that formed part of the submission to the position in question.

## Technologies
This pipeline makes use of the following languages, applications, and libraries:
* Python
  * requests
  * pandas
  * BeautifulSoup

## Running the Project
This pipeline requires on a number of special variables, such as the API port and specific hardcoded values used in some API calls, to function properly. For privacy reasons these secret variables are obfuscated and not present in this repository. I may release these variables in the future when I feel the time is right.