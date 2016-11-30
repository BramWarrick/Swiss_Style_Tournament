## File Format
* Installation
* High Level Structure
* Rationale
* General Notes

## Installation
Required:  
_Python 2.7 with psycopg2 installed_  
_PSQL_  

* Use psql to import tournament (`\i tournament.sql`)
* Exit psql
* Enter python
* Use tournament_test.py to verify conditions are met


## High Level Structure
  
Tournaments are created and contain rounds - a grouping of matches where players are grouped by skill (W/L within tournament). Each round holds as many matches as needed to keep all players engaged with only one bye, if necessary.  
  
No player will get more than one bye in the course of the tournament.  
  
Data structure (in short):
tournaments>rounds>matches>match_assignments
players>tournament_registrants>match_assignments
match_assignments>match_role_types
match_assignments>Match_result_types

I created a number of suplemental VIEWS, partially because I dislike subSELECTS over a certain size, so exclusion views were given a layered treatment.


## Rationale
Designed to handle all of the above-and-beyond criteria. Because of this, the datastructure is different than assumed in the test scenarios.  
  
I made minor tweaks, so that it could run with multiple iterations and additional tournaments while holding all history.  
  
The amount of code may be on the high side, but I wanted to experiment with creating some True/False functions for validations.  
  
Some functions were originally written to give me feedback, but I dialed that in. Comments help explain choices - if you're deeply interested.  



