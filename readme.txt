Notes:
I set this up to handle all of the above-and-beyond criteria.
The datastructure is different than assumed in the test scenarios.
I made minor tweaks, so that it could run with multiple iterations and additional tournaments.
This is an insane amount of code (1000+ lines) for the project, but... I wanted to kick the tires on creating some T/F functions for validations.
Some functions were originally written to give me feedback, but I dialed that in. Comments help explain choices - if you're deeply interested.

Data structure (in short):
tournaments>rounds>matches>match_assignments
players>tournament_registrants>match_assignments
match_assignments>match_role_types
match_assignments>Match_result_types

There are a lot of VIEWS, partially because I dislike subSELECTS past a certain size, so exclusion views were given a layered treatment.

Steps to set up project:
use psql to import tournament (\i tournament.sql)
exit psql
enter python
user tournament_test.py to verify conditions are met

Usage:
new__ runs logic to create what's in __ - typically an abstracted layer of logic
get__ returns a value
add__ creates the __ in a table
update__ updates a table; since it's not an add, I didn't want to call it that
is__ is a validation, it's fairly spelled out; returns T/F
exists__ is a validation, it's fairly spelled out; returns T/F

I may post to the forum. I'm lazy so I created a t.py file that would import from tournament_test (which imports from tournament).
This allowed for much shorter rounds of typing. I never want to type "tournament" again. SO. MUCH. "tournmaent" It looks like torment, because it is. :-)

Thank you - this was useful. Feedback is welcome.

Biggest takeaways:
Time estimation - continue to triple my estimate
Code drift - I started to trend a little UI side with my "print"s; pulled that back
Lots of code things, mostly PostGreSQL since my experience was with Oracle - Good stuff