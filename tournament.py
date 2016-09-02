#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import time
import random

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    conn = psycopg2.connect(database="tournament")
    return conn

def newAllTheThings():
    # Create tournament
    # Accept registrants
    # Create tournament round - closing tournament registration
    # Enter results
    # Create next round (until total needed is met)
    # return results
    return "I'm a thought"

def getTournamentId():
    """Created to modify the test sceanrios - allowing a tournament_id to be passed in"""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT MAX(tournament_id) current_tournament 
            FROM tournaments
        """)

    current_tournament = cursor.fetchone()
    conn.close
    current_tournament = int(current_tournament[0])

    return current_tournament

def getRoundId(tournament_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT MAX(trml.round_id) as round_id 
            FROM tournament_round_match_list trml
            WHERE trml.tournament_id = (%s)
        """,(tournament_id,))

    recent_round = cursor.fetchone()
    conn.close
    recent_round = int(recent_round[0])

    return recent_round

def newTournament(tournament_desc=None, tournament_date=None):
    """Abstracted layer - runs logic for creating tournaments; receives two optional parameters

    Args:
      tournament_desc: Optional entry, describing tournament (e.g. 'Soccer Match 9/1/2016')
      tournament_date:  Optional entry, date the tournament will occur - defaults to system date; used in description if empty
    """

    if tournament_date is None:
        tournament_date = time.strftime("%m/%d/%Y")

    if tournament_desc is None:
        tournament_desc = "Tournament on " + str(tournament_date)

    result = addTournament(tournament_desc, tournament_date)
    return result

def addTournament(tournament_desc, tournament_date):
    """Creates a new tournament; receives two optional parameters

    Args:
        tournament_desc: Optional entry, describing tournament (e.g. 'Soccer Match 9/1/2016')
        tournament_date:  Optional entry, date the tournament will occur - defaults to system date; used in description if empty
    Returns:
        tournament_id:  tournament_id of the newly created tournament; allowed easier debugging
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        INSERT INTO tournaments
        (tournament_desc, tournament_date) 
        VALUES (%s,%s)
        RETURNING tournament_id
    """,(tournament_desc, tournament_date,))

    conn.commit()
    results = cursor.fetchone()
    conn.close

    return results[0]

def registerPlayer(tournament_id, player_name):
    """Abstracted layer - runs logic for user registration with UI interaction

    If player_name is not found, user is prompted (y,N) if user should be added.
    If player name is found, user is prompted if returning player or to create new player.

    Args:
        tournament_id: tournament_id value from tournaments table.
        player_name: the player's full name (need not be unique).
    Returns:
        Exception type messaging
    """

    if not existsTournamentId(tournament_id):
        return "Tournament id " + str(tournament_id) + " does not exist."

    if not isAcceptingRegistrants(tournament_id):
        return "Tournament id " + str(tournament_id) + "is closed to registrants"

    if not existsPlayerName(player_name):
        player_id = addPlayer(player_name)
    else:
        #
        # Lines commented out below would handle a more real-world solution, perhaps with messages to the front end
        #
        # player_id = existingPlayerNameDeconflict(player_name)
        player_id = addPlayer(player_name)
        # if isPlayerRegistered(tournament_id, player_id):
        #     return player_name + " is already registered for this tournament."
    if player_id != None:
        addTournamentRegistrant(tournament_id, player_id)
    else:
        return "\n\n" + player_name + " was not registered, per user input."

def existsTournamentId(tournament_id):
    """Simple failsafe to prevent attempted registration into a nonexistant tournament

    Args:
        tournament_id: tournament_id, for validation if present in tournaments table
    Returns:
        True/False: True if present; else False
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT COUNT(*) as count 
            FROM tournaments
            WHERE tournament_id = (%s)
        """,(tournament_id,))

    results = cursor.fetchone()
    conn.close
    results = results[0]

    if results == 0:
        return False
    else:
        return True

def isAcceptingRegistrants(tournament_id):
    """Returns False if registration is closed (rounds and matches have started)

    Args:
        tournament_id: tournament_id, used to determine if rounds have been created (a sure sign that teh tournament has begun)
    Returns:
        True/False: True if no rounds found for tournament_id; else False
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        SELECT COUNT(*) as count
        FROM rounds
        WHERE tournament_id = %s
    """,(tournament_id, ))
    
    results = cursor.fetchone()
    conn.close

    if results[0] == 0:
        return True
    else:
        return False

def existsPlayerName(player_name):
    """Returns True if player_name is found in players table.

    Used for preliminary validations; player_id is checked elsewhere.

    Args:
        name: the player's full name (need not be unique).
    Returns:
        True/False: If the name is in the list return True, else False
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT count(*) as count 
            FROM players
            WHERE player_name = (%s)
        """,(player_name,))

    results = cursor.fetchone()
    conn.close
    results = results[0]

    if results == 0:
        return False
    else:
        return True

def isPlayerRegistered(tournament_id, player_id):
    """Returns True if player_id is registered in tournament

    Used in validations to prevent an attempt to re-register - allows appropriate text prompt to user.

    Args:
        tournament_id: used as one part of the primary key to the tournament_registrants table
        player_id: second part of primary key to the tournament_registrants table
    Returns:
        True/False: if player is registered return True; else False
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT count(*) as count 
            FROM tournament_registrants
            WHERE tournament_id = %s
            AND player_id = (%s)
        """,(tournament_id, player_id))

    results = cursor.fetchone()
    results = results[0]
    conn.close

    if results == 0:
        return False
    else:
        return True

def existingPlayerNameDeconflict(player_name):
    """Asks user if player is a returming player. Returns player_id.
    Handles some exceptins would normally be front end-back end conversation

    Logic is only used if the player_name already exists in database!
    getPlayerIdUserSelection runs a user prompt with player list and returns the player_id

    Args:
        player_name: the player's full name (need not be unique).
    """
    answer_list = ['y','N','cancel']
    returning_player = ""
    print "Type 'cancel' to escape.\n\n"
    while returning_player not in answer_list:
        # This needs more work - add if new player, otherwise look up their player_id
        returning_player = raw_input("Is this a returning player (y,N)?")

    if returning_player.lower() == 'cancel':
        return None
    elif returning_player == 'N':
        print player_name + " was added!"
        return addPlayer(player_name)
    else:
        return getPlayerIdUserSelection(player_name)

def getPlayerIdUserSelection(player_name):
    """Runs a user prompt with player list and returns the player_id, based on user entry

    Part of the logic to resolve multiple users with same name.

    Args:
        player_name: the player's full name (need not be unique).
    Returns:
        player_id: after user prompt and response to select correct user.
    """
    choice_list = getPlayerListForName(player_name)
    return getPlayerIdDisplay(choice_list)

def getPlayerListForName(player_name):
    """Returns a list of players with the same name - date/time created is used to distinguish

    Part of the logic to resolve multiple users with same name.

    Args:
        player_name: the player's full name (need not be unique).
    Returns:
        clhoice_list: list of lists - each entry has all the components to build a user prompt (selection number, name, date/time created, player_id (kept hidden))
    """
    choice_list = []

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT player_name
            , player_create_datettime
            , player_id
            FROM players
            WHERE player_name = (%s)
        """,(player_name,))

    results = cursor.fetchall()
    conn.close

    i = 1
    for item in results:
        choice_list.append([i,results[i-1][0],results[i-1][1],results[i-1][2]])
        i += 1

    return choice_list

def getPlayerIdDisplay(choice_list):
    """Returns player_id after user selection or None if they cancel
    Needed for testing - would normally be front end that handles UI, I'd just pass in the list

    Part of the logic to resolve multiple users with same name.

    Args:
        choice_list: list of lists - each entry has all the components to build a user prompt (selection number, name, date/time created, player_id (kept hidden))
    Returns:
        player_id or None: after user selection, player_id is returned; if they cancel None is returned. 
    """
    approved_answers = ['cancel']
    user_prompt = "Please select from one of the below choices:\n\n"
    user_prompt = "          Name......................Date Entered\n\n"
    for player in choice_list:
        date = player[2].strftime('%c')
        user_prompt += "   " + str(player[0]) + ")   " + str(player[1])
        user_prompt += "." * (40 - len(player[1]) - len(date))
        user_prompt += date + "\n\n"
        approved_answers.append(player[0])
    print user_prompt

    answer = ""
    while answer not in approved_answers:
        answer = raw_input("Which of the above players is the correct person?")
        if answer.lower == 'cancel':        # Needs to be here, otherwise code will .lower an integer which is not allowed
            return None
        elif answer.isdigit():
            # Is numberic, so convert this over to int
            answer = int(answer)
    
    return choice_list[answer-1][3]

def addPlayer(player_name):
    """Adds a player to the tournament database and returns the new player_id.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
        player_name: the player's full name (need not be unique).
    Returns:
        player_id: the player_id of the newly created player; used in subsequent logic
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        INSERT INTO players (player_name) 
        VALUES (%s)
        RETURNING player_id
    """,(player_name,))

    conn.commit()
    results = cursor.fetchone()

    conn.close

    return results[0]

def addTournamentRegistrant(tournament_id, player_id):
    """Adds a player_id to the tournament_registrant table.

    Args:
        tournament_id: tournament_id value from tournaments table (primary key)
        player_id: player_id value from the players table (primary key)
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        INSERT INTO tournament_registrants
        (tournament_id, player_id) 
        VALUES (%s,%s)
    """,(tournament_id, player_id))
    conn.commit()
    conn.close

def newRound(tournament_id):
    """Abstracted layer - runs logic for creating a new round in the tournament

    Args:
        tournament_id: rounds will be created for this tournament
    """
    if not isLastRoundComplete(tournament_id):
        return
    if not isRoundNeeded:
        return
    if getRegistrantCount(tournament_id) < 2:
        return
    new_round_id = addNextRound(tournament_id)
    newMatchesForRound(tournament_id, new_round_id)
    newMatchAssignments(tournament_id, new_round_id)
    return new_round_id

def isLastRoundComplete(tournament_id):
    """Returns True/False based on if all previous matches are complete

    Required in order to rank players for best-match competitions

    Args:
        tournament_id: tournament_id value from tournaments table (primary key)
    Returns:
        True/False: if tournament has no rounds with incomplete matches, return True, else False
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT COUNT(*)
            FROM rounds_incomplete
            WHERE tournament_id = (%s)
        """,(tournament_id,))

    results = cursor.fetchone()
    results = results[0]
    conn.close

    if results == 0:
        return True
    else:
        return False

def isRoundNeeded(tournament_id):
    """Returns True/False if more rounds are needed

    Quantifies rounds created and compares to the number of registrants; powers of 2

    Args:
        tournament_id: tournament_id used to 
    Returns:
        True/False: True if number of rounds is below threshold for total matches; else False
    """
    round_count = getRoundCount(tournament_id)
    registrant_count = getRegistrantCount(tournament_id)
    if 2 ** round_count < registrant_count:
        return True
    else:
        return False

def getRoundCount(tournament_id):
    """Returns count of rounds created so far, for tournament_id.

    Used in math of creating matches and rounds.

    Args:
      tournament_id: tournament_id from tournaments table, uniquely identifying tournament.
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT count(*) as count 
            FROM rounds
            WHERE tournament_id = (%s)
        """,(tournament_id,))

    results = cursor.fetchone()
    results = int(results[0])
    conn.close

    return results

def getRegistrantCount(tournament_id):
    """Returns count of registrants for tournament_id.

    Used in math of creating matches and rounds.

    Args:
      tournament_id: tournament_id from tournaments table, uniquely identifying tournament.
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT count(*) as count 
            FROM tournament_registrants
            WHERE tournament_id = (%s)
        """,(tournament_id,))

    results = cursor.fetchone()
    results = int(results[0])
    conn.close

    return results

def addNextRound(tournament_id):
    """Adds a new round to the tournament and returns the new round_id.

    Args:
        tournament_id: the tournament user is currently managing.
    Returns:
        round_id: newly created round_id is returned; used in subsequent logic
    """
    round_number = getRoundCount(tournament_id) + 1
    round_desc = "Round " + str(round_number)

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            INSERT INTO rounds 
            (tournament_id, round_number, round_desc) 
            VALUES (%s,%s,%s)
            RETURNING round_id
        """,(tournament_id, round_number, round_desc))

    conn.commit()
    results = cursor.fetchone()
    conn.close

    return results[0]

def newMatchesForRound(tournament_id, round_id):
    """Abstracted layer, runs logic for adding matches to the round.

    Args:
        tournament_id: tournament_id value from tournaments table (primary key)
        round_id: matches are created within this round_id
    Returns:
        number of matches created
    """
    match_id = 0
    while match_id * 2 < getRegistrantCount(tournament_id):
        addMatch(round_id, "Match " + str(match_id + 1))
        match_id += 1
    return match_id

def addMatch(round_id, match_desc):
    """Adds a match to the matches table

    Args:
        round_id: matches are created within this round_id
        match_desc: description for the human readable in matches table
    """
    conn = connect()
    cursor = conn.cursor()

    high_score_first_move = random.choice([True, False])
    cursor.execute(
    """
        INSERT INTO matches
        (round_id, match_desc, match_high_score_first) 
        VALUES (%s,%s,%s)
    """,(round_id, match_desc, high_score_first_move))

    conn.commit()
    conn.close

def newMatchAssignments(tournament_id, round_id):
    """Abstracted layer for logic to create player assignments.

    Loops through created matches
        gets best, unassigned player
        gets best player based on score - has not played player previously

    Args:
        tournament_id: tournament_id value from tournaments table (primary key)
        round_id: all matches are created within this round_id
    """
    match_list = getMatchList(tournament_id, round_id)
    for match in match_list:
        player1 = getUnassignedPlayer(tournament_id, round_id)
        player2 = getUnmatchedPlayer(tournament_id, round_id, player1)
        if player2 == None:
            addMatchAssignments(match[0], player1, 'B','B')      # User gets a Bye
            return
        # If player 1 goes first, create with appropriate role
        if match[1] == True:
            addMatchAssignments(match[0], player1, 'F')     # first
            addMatchAssignments(match[0], player2, 'S')     # second
        else:
            addMatchAssignments(match[0], player1, 'S')     # second
            addMatchAssignments(match[0], player2, 'F')     # first
    return

def getUnassignedPlayer(tournament_id, round_id):
    """Returns top ranked, player not yet assigned to a match in this round.

    Args:
        tournament_id: tournament_id value from tournaments table (primary key)
        round_id: all matches and assignments are created within this round_id
    Returns:
        player_id: top ranked player - ranked by score, then wins (when byes occur score > wins)
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        SELECT trpu.player_id
        FROM tournament_round_players_unassigned trpu
        WHERE trpu.tournament_id = %s
        AND trpu.round_id = %s
        ORDER BY trpu.score DESC
        , trpu.player_id
        LIMIT 1
    """,(tournament_id, round_id,))

    results = cursor.fetchone()
    conn.close

    return results[0]

def getUnmatchedPlayer(tournament_id, round_id, player_id):
    """Returns top ranked, player not yet assigned AND that hasn't played player_id in this tournament

    Args:
        tournament_id: tournament_id value from tournaments table (primary key)
        player_id: used to eliminate players that have previously competed in tournament_id
    Returns:
        player_id: best-match player - ranked by score, then wins (when byes occur: score > wins)
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        SELECT tpu.candidate_unmatched
        FROM tournament_player_unmatched tpu
        WHERE tpu.tournament_id = %s
        AND tpu.round_id = %s
        AND tpu.player_id = %s
        ORDER BY tpu.candidate_score DESC
        , tpu.candidate_unmatched
        LIMIT 1
    """,(tournament_id, round_id, player_id))

    results = cursor.fetchone()
    conn.close

    if results != None:
        results = results[0]

    return results

def addMatchAssignments(match_id, player_id, match_role_id, match_result_id=None):
    """Adds match assignments to the match_assignments table

    Args:
        match_id: players will be assigned to this match
        player_id: player who is in this match
        match_role_id: moves first, second or bye
        match_result_id: Optional, only value passed in is 'B' for Bye. No need to wait for results of game - enter result.
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        INSERT INTO match_assignments
        (match_id, player_id, match_role_id, match_result_id)
        VALUES (%s, %s, %s, %s)
    """,(match_id, player_id, match_role_id, match_result_id))

    conn.commit()
    conn.close

    return

def getMatchList(tournament_id, round_id):
    """Returns list of all matches created for round_id, with flag for high_score_moves_first (T/F)

    Args:
        tournament_id: all matches occur within this tournament
        round_id: all matches and assignments are created within this round_id
    Returns:
        match_list: full list of matches, with flag for high_score_moves_first (T/F)
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        SELECT trml.match_id
        , match_high_score_first
        FROM tournament_round_match_list trml
        , matches m
        WHERE trml.match_id = m.match_id
        AND trml.tournament_id = %s
        AND trml.round_id = %s
        ORDER BY trml.match_id
    """,(tournament_id, round_id,))

    match_list = cursor.fetchall()
    conn.close

    return match_list

def newMatchResults(match_id, winner, loser, draw=False):
    """Abstracted layer - runs logic for writing game results to match_assgnments table

    Args:
        match_id: id for the game being reported
        winner: player who won; if draw, order will not matter
        loser: player who lost; if draw, order will not matter
        draw: Optional, only returned if a draw; allows logic to handle ties/stalemates
    """
    if not draw:
        addMatchResults(match_id, winner, "W")
        addMatchResults(match_id, loser, "L")
    else:
        addMatchResults(match_id, winner, "D")
        addMatchResults(match_id, loser, "D")

def updateMatchResults(match_id, player_id, match_result_id):
    """Writes the results to the match_assignments table

    Args:
        match_id: match with results to report
        player_id: player whose results are being written
        match_result_id: can be win, loss, bye or draw
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        UPDATE match_assignments
        SET match_result_id = %s
        WHERE match_id = %s
        AND player_id = %s
    """,(match_result_id, match_id, player_id))

    conn.commit()
    conn.close

    return

def deleteMatches(tournament_id):
    """Remove all the match records from the tournament_id."""

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            DELETE FROM match_assignments 
            WHERE match_id IN (SELECT match_id
                                FROM tournament_round_match_list trml
                                WHERE trml.tournament_id = %s)
        """, (tournament_id,))
    conn.commit()

    cursor.execute(
        """
            DELETE FROM matches 
            WHERE match_id IN (SELECT match_id
                                FROM tournament_round_match_list trml
                                WHERE trml.tournament_id = %s)
            """, (tournament_id,))
    conn.commit()

    cursor.execute(
        """
            DELETE FROM rounds
            WHERE round_id IN (SELECT round_id
                                FROM tournament_round_match_list trml
                                WHERE trml.tournament_id = %s)
        """, (tournament_id,))
    conn.commit()

    conn.close

def deletePlayers(tournament_id):
    """Deletes all players in tournament_id

    Args:
        tournament_id: allows a check to ensure the tournament has no players (recently created by 'deleteMatches()')"""
    
    # deleteMatches must be done in order to protect integrity
    # Players were entered into match_assignment table, so they must be removed
    deleteMatches(tournament_id)

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            DELETE FROM tournament_registrants
            WHERE tournament_id = %s
        """, (tournament_id,))
    conn.commit()

    conn.close

def countPlayers(tournament_id):
    """Returns the number of players currently registered to the tournament.

    Needed to change in order to accommodate the test script.

    Tournaments can stack, so player count isn't /required/ to be equal to people registered"""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT COUNT(*) AS count 
            FROM tournament_registrants tr
            WHERE tr.tournament_id = %s
        """,(tournament_id,))

    # Normal counting of players, below
    # cursor.execute(
    #     """
    #         SELECT COUNT(*) AS count 
    #         FROM players 
    #     """)

    results = cursor.fetchone()
    results = int(results[0])
    conn.close

    return results

def playerStandings(tournament_id):
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    
    #tournament_test.py assumes matches are created automatically, rather than 
    if getRoundCount(tournament_id) == 0:
        newRound(tournament_id)

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT ts.player_id
            , ts.player_name
            , ts.player_wins
            , ts.matches_played
            FROM tournament_score ts
            WHERE ts.tournament_id = %s
            ORDER BY ts.score DESC 
            , ts.player_wins DESC
        """,(tournament_id,))

    results = cursor.fetchall()
    conn.close

    return results

def reportMatch(tournament_id, winner, loser):
    """Records the outcome of a single match between two players.

    Args:
        tournament_id: tournament currently running
        winner:  the id number of the player who won
        loser:  the id number of the player who lost
    """

    # Add logic to find match, within tournament_id where both players compete
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT MAX(trml.match_id) as round_id 
            FROM tournament_round_match_list trml
            ,  (SELECT ma.match_id
                FROM match_assignments ma
                WHERE ma.player_id = (%s)
                AND ma.match_result_id IS NULL) ma1
            ,  (SELECT ma.match_id
                FROM match_assignments ma
                WHERE ma.player_id = (%s)
                AND ma.match_result_id IS NULL) ma2
            WHERE trml.tournament_id = (%s)
            AND trml.match_id = ma1.match_id
            AND trml.match_id = ma2.match_id
        """,(winner, loser, tournament_id))

    match_id = cursor.fetchone()
    conn.close
    if match_id != None:
        match_id = int(match_id[0])
        updateMatchResults(match_id, winner, 'W')
        updateMatchResults(match_id, loser, 'L')

def swissPairings(tournament_id, round_id):
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    This logic handles Byes within the swiss_pairing view created by tournament.sql

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT sp.player1
            , sp.player1_name
            , sp.player2
            , sp.player2_name
            FROM swiss_pairings sp
            WHERE sp.tournament_id = (%s)
            AND sp.round_id = (%s)
        """,(tournament_id, round_id))

    swiss_pairings = cursor.fetchall()
    conn.close

    return swiss_pairings