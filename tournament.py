#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import time
import random

try:
    conn = psycopg2.connect(database="tournament") #, user="vagrant", host="localhost", port="8000")
    # conn = psycopg2.connect("dbname=tournament port=8000")
except:
    print "I am unable to connect to the database"

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    conn = psycopg2.connect(database="tournament")
    return conn

def userPrompt():
    # User prompt
    # Create tournament
    # Accept registrants
    # Create tournament round - closing tournament registration
    # Enter results
    # Create next round (until total needed is met)
    # Display results
    return "I'm a stub"

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
    current_tournament = int(results[0])

    return current_tournament

def newTournament(tournament_desc=None, tournament_date=None):
    if tournament_date is None:
        tournament_date = time.strftime("%m/%d/%Y")

    if tournament_desc is None:
        tournament_desc = "Tournament on " + str(tournament_date)

    result = addTournament(tournament_desc, tournament_date)
    return result

def addTournament(tournament_desc, tournament_date):

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
    """Abstracted layer - runs logic for user registration.

    If player_name is not found, user is prompted (y,N) if user should be added.
    If player name is found, user is prompted if returning player or to create new player.

    Args:
        tournament_id: tournament_id value from tournaments table.
        player_name: the player's full name (need not be unique).
    """

    if not existsTournamentId(tournament_id):
        return "Tournament id " + str(tournament_id) + " does not exist."

    if not isAcceptingRegistrants(tournament_id):
        return "Tournament id " + str(tournament_id) + "is closed to registrants"

    if not existsPlayerName(player_name):
        player_id = newPlayerConfirmation(player_name)
    else:
        player_id = existingPlayerNameDeconflict(player_name)
        if isPlayerRegistered(tournament_id, player_id):
            print player_name + " is already registered for this tournament."
            return
    if player_id != None:
        addTournamentRegistrant(tournament_id, player_id)
    else:
        print "\n\n" + player_name + " was not registered, per user input."

def existsTournamentId(tournament_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT count(*) as count 
            FROM tournaments
            WHERE tournament_id = (%s)
        """,(tournament_id,))

    results = cursor.fetchone()
    results = results[0]
    conn.close

    if results == 0:
        return False
    else:
        return True

def isAcceptingRegistrants(tournament_id):
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
    """Returns True if player_name is found in players table.

    Used for preliminary validations; player_id is checked elsewhere.

    Args:
      name: the player's full name (need not be unique).
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

def newPlayerConfirmation(player_name):
    """Asks user if player is a returming player. Returns player_id.

    We should only see this logic used if the player_name already exists in database!

    Args:
        player_name: the player's full name (need not be unique).
    """
    answer_list = ['y','N','cancel']
    add_player = ""
    print "Type 'cancel' to escape.\n\n"
    while add_player not in answer_list:
        # This needs more work - add if new player, otherwise look up their player_id
        add_player = raw_input("Player not found in list. Add '" + player_name + "'?' (y,N)?")

    if add_player.lower() == 'cancel':
        return None
    elif add_player == 'y':
        return addPlayer(player_name)
    else:
        return None

def existingPlayerNameDeconflict(player_name):
    """Asks user if player is a returming player. Returns player_id.

    We should only see this logic used if the player_name already exists in database!

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
        return addPlayer(player_name)
    else:
        return getPlayerIdUserSelection(player_name)

def getPlayerIdUserSelection(player_name):
    choice_list = getPlayerListForName(player_name)
    return getPlayerIdDisplay(choice_list)

def getPlayerListForName(player_name):
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
    print results

    i = 1
    for item in results:
        choice_list.append([i,results[i-1][0],results[i-1][1],results[i-1][2]])
        i += 1

    print choice_list
    return choice_list

def getPlayerIdDisplay(choice_list):
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
        if answer.lower == 'cancel':
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
      name: the player's full name (need not be unique).
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
    if not isLastRoundComplete(tournament_id):
        print "The previous round is not complete."
        print "Please finish entering all the results."
        return
    if not isRoundNeeded:
        print "Tournament complete!"
        # print "The results are:"
        return
    new_round_id = addNextRound(tournament_id)
    newMatchesForRound(tournament_id, new_round_id)
    newMatchAssignments(tournament_id, new_round_id)

def isLastRoundComplete(tournament_id):
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
    match_id = 0
    while match_id * 2 < getRegistrantCount(tournament_id):
        addMatch(round_id, "Match " + str(match_id + 1))
        match_id += 1
    if match_id == 1:
        print "Round " + str(round_id) + " created with " + str(match_id) + " match."
    else:
        print "Round " + str(round_id) + " created with " + str(match_id) + " matches."

def addMatch(round_id, match_desc):
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
    match_list = getMatchList(tournament_id, round_id)
    for match in match_list:
        player1 = getUnassignedPlayer(tournament_id, round_id)
        player2 = getUnmatchedPlayer(tournament_id, player1)
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

    return results

def getUnmatchedPlayer(tournament_id, player_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        SELECT tpu.candidate_unmatched
        FROM tournament_player_unmatched tpu
        WHERE tpu.tournament_id = %s
        AND tpu.player_id = %s
        ORDER BY tpu.candidate_score DESC
        , tpu.candidate_unmatched
        LIMIT 1
    """,(tournament_id, player_id))

    results = cursor.fetchone()
    conn.close

    return results

def addMatchAssigments(match_id, player_id, match_role_id, match_result_id=None):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        INSERT INTO match_assignments ma
        (match_id, player_id, match_role_id, match_result_id)
        VALUES (%s, %s, %s, %s)
    """,(match_id, player_id, match_role_id, match_result_id))

    conn.commit()
    conn.close

    return

def getMatchList(tournament_id, round_id):
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

    results = cursor.fetchall()
    conn.close

    return results

def newMatchResults(match_id, winner, loser, draw=False):
    if not draw:
        addMatchResults(match_id, winner, "W")
        addMatchResults(match_id, loser, "L")
    else:
        addMatchResults(match_id, winner, "D")
        addMatchResults(match_id, loser, "D")

def addMatchResults(match_id, player_id, match_result_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
    """
        UPDATE match_assignments ma
        SET match_result_id = %s
        WHERE ma.match_id = %s
        AND ma.player_id = %s)
    """,(match_result_id, match_id, player_id))

    conn.commit()
    conn.close

    return

def deleteMatches():
    """Remove all the match records from the database."""

def deletePlayers():
    """Remove all the player records from the database."""

def countPlayers():
    """Returns the number of players currently registered."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT COUNT(*) AS count 
            FROM players
        """)

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
    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT p.player_id
            , p.player_name
            , ts.score
            , ts.player_wins
            , ts.matches_played
            FROM tournament_score ts
            , player p
            WHERE ts.player_id = p.player_id
            AND tournament_id = %s
            ORDER BY ts.score DESC
        """,(tournament_id,))

    results = cursor.fetchone()
    results = int(results[0])
    conn.close

    return results

def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    newMatchResults(match_id, winner, loser)

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
