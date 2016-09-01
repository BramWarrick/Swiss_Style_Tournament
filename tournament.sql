-- Table definitions for the tournament project.
--
-- Put your SQL 'CREATE TABLE' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

-- DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;
-- DATABASE CREATED, NOW LOG IN
\c tournament;

-- DROP TABLES IF EXIST; TOGGLE ON/OFF IN CODE
DROP TABLE IF EXISTS match_assignments CASCADE;
DROP TABLE IF EXISTS match_result_types CASCADE;
DROP TABLE IF EXISTS match_roles CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS rounds CASCADE;
DROP TABLE IF EXISTS tournament_registrants CASCADE;
DROP TABLE IF EXISTS tournaments CASCADE;
DROP TABLE IF EXISTS players CASCADE;

-- CREATE TABLES
CREATE TABLE tournaments (
	tournament_id serial PRIMARY KEY,
	tournament_desc text,
	tournament_date date DEFAULT current_date,
	tournament_complete boolean
	);

CREATE TABLE players (
	player_id serial PRIMARY KEY,
	player_name text,
	player_create_datettime timestamp DEFAULT current_timestamp
	);

CREATE TABLE tournament_registrants (
	tournament_id integer REFERENCES tournaments,
	player_id integer REFERENCES players,
	PRIMARY KEY (tournament_id, player_id)
	);

CREATE TABLE rounds (
	tournament_id integer REFERENCES tournaments,
	round_id serial PRIMARY KEY,
	round_number integer,
	round_desc text
	);

CREATE TABLE match_result_types (
	match_result_id text PRIMARY KEY,
	match_result_desc text UNIQUE,
	match_result_modifier numeric(2,1)
	);

CREATE TABLE match_roles (
	match_role_id text PRIMARY KEY,
	match_role text UNIQUE
	);

CREATE TABLE matches (
	round_id integer REFERENCES rounds,
	match_id serial PRIMARY KEY,
	match_desc text,
	match_high_score_first boolean
	);

CREATE TABLE match_assignments (
	match_id integer REFERENCES matches,
	player_id integer REFERENCES players,
	match_role_id text REFERENCES match_roles,
	match_result_id text REFERENCES match_result_types,
	PRIMARY KEY (match_id, player_id)
	);

-- POPULATE TABLES WITH REFERENCE VALUES
-- Populate match_result_types with human readable and math VALUES
INSERT INTO match_result_types (match_result_id, match_result_desc, match_result_modifier) VALUES ('B','Bye',1);
INSERT INTO match_result_types (match_result_id, match_result_desc, match_result_modifier) VALUES ('W','Win',1);
INSERT INTO match_result_types (match_result_id, match_result_desc, match_result_modifier) VALUES ('D','Draw',.5);
INSERT INTO match_result_types (match_result_id, match_result_desc, match_result_modifier) VALUES ('L','Loss',0);

-- Populate match_roles with two VALUES: first and second for their role in game (who starts first)
INSERT INTO match_roles (match_role_id, match_role) VALUES ('F','First');
INSERT INTO match_roles (match_role_id, match_role) VALUES ('S','Second');
INSERT INTO match_roles (match_role_id, match_role) VALUES ('B','Bye');

-- CREATE VIEWS

-- Create a view linking tournaments-rounds-matches since the normal form made that a bit of work
CREATE OR REPLACE VIEW tournament_round_match_list AS
	SELECT r.tournament_id
	, r.round_id
	, r.round_desc
	, m.match_id
	, m.match_desc
	FROM matches m
	, rounds r
	WHERE m.round_id = r.round_id
	;

-- Create a view bringing together match information, joined appropriately for match results
CREATE OR REPLACE VIEW match_result_details AS
	SELECT trml.tournament_id
	, trml.round_id
	, ma.match_id
	, ma.player_id
	, ma.match_role_id
	, ma.match_result_id
	, COALESCE(mrt.match_result_desc, 'Unfinished')
	, COALESCE(mrt.match_result_modifier, 0) match_result_modifier
	FROM match_assignments ma
		LEFT OUTER JOIN match_result_types mrt ON (ma.match_result_id = mrt.match_result_id)
	, tournament_round_match_list trml
	WHERE ma.match_id = trml.match_id
	;

-- Create a view that shows tournament/rounds where the match is still open (needs more results)
CREATE OR REPLACE VIEW rounds_incomplete AS
	SELECT trml.tournament_id 
	, trml.round_id
	FROM match_assignments ma
	, tournament_round_match_list trml
	WHERE ma.match_id = trml.match_id
	AND ma.match_result_id IS NULL
	GROUP BY trml.tournament_id 
	, trml.round_id
	;

-- Create a view, returns all tournament/rounds that aren't in the rounds_incomplete view; therefore complete
CREATE OR REPLACE VIEW rounds_complete AS 
	SELECT r.tournament_id
	, m.round_id
	FROM match_assignments ma
	, rounds r
	, matches m LEFT OUTER JOIN rounds_incomplete ri ON (m.round_id = ri.round_id)
	WHERE ma.match_id = m.match_id
	AND m.round_id = r.round_id
	AND ri.round_id IS NULL
	GROUP BY r.tournament_id
	, m.round_id
	;

-- Create a view, returns score for all tournaments in database where the match has been created
CREATE OR REPLACE VIEW tournament_score AS
	SELECT tr.tournament_id
	, tr.player_id
	, p.player_name
	, COALESCE(SUM(mrd.match_result_modifier),0) score
	, COALESCE(SUM(CASE WHEN mrd.match_result_id = 'W' then 1 else 0 end),0) player_wins
	, COALESCE(SUM(CASE WHEN mrd.match_result_id IS NOT NULL then 1 else 0 end),0) matches_played
	FROM tournament_registrants tr
		LEFT OUTER JOIN match_result_details mrd ON (tr.player_id = mrd.player_id AND tr.tournament_id = mrd.tournament_id)
	, players p
	WHERE tr.player_id = p.player_id
	GROUP BY tr.tournament_id
	, tr.player_id
	, p.player_id
	ORDER BY tr.tournament_id
	, COALESCE(SUM(mrd.match_result_modifier),0) DESC
	, COALESCE(SUM(CASE WHEN mrd.match_result_id = 'W' then 1 else 0 end),0) DESC
	, COALESCE(SUM(CASE WHEN mrd.match_result_id IS NOT NULL then 1 else 0 end),0) DESC
	, tr.player_id
	;

-- Create a view, all players in a round that have not been assigned to a match
CREATE OR REPLACE VIEW tournament_round_players_assigned AS
	SELECT trml.round_id
	, tr.player_id
	FROM tournament_registrants tr
	, tournament_round_match_list trml
	, match_assignments ma
	WHERE tr.tournament_id = trml.tournament_id
	AND trml.match_id = ma.match_id
	;

-- Create a view, returns all players in the tournament, that have not been assigned to a round/match
CREATE OR REPLACE VIEW tournament_round_players_unassigned AS
	SELECT trml.tournament_id
	, trml.round_id
	, tr.player_id
	, ts.score
	FROM tournament_registrants tr 
		LEFT OUTER JOIN	tournament_round_players_assigned trpa ON (tr.player_id = trpa.player_id)
		LEFT OUTER JOIN tournament_score ts ON (tr.player_id = ts.player_id)
	, tournament_round_match_list trml
	WHERE tr.tournament_id = trml.tournament_id
	AND trpa.player_id IS NULL
	ORDER BY trml.tournament_id
	, trml.round_id
	, ts.score DESC 				-- This sort allows Byes to float to the top, score>wins, lower frequency of repeat Byes
	, ts.player_wins DESC 	-- This sort allows Byes to float to the top, score>wins, lower frequency of repeat Byes
	, tr.player_id 					-- Tie breaker
	;

-- Create a view, returns all players registered for tournament that can be paired with player_id
CREATE OR REPLACE VIEW tournament_match_candidate AS
	SELECT tr.tournament_id 
	, tr.player_id
	, tr2.player_id candidate
	FROM tournament_registrants tr
	, tournament_registrants tr2
	WHERE tr.tournament_id = tr2.tournament_id
	AND tr.player_id <> tr2.player_id
	;

-- Create a view, returns all players that played player_id previously in THIS tournament
CREATE OR REPLACE VIEW tournament_player_matched AS
	SELECT trml.tournament_id
	, p1.player_id
	, p2.player_id played_previously
	FROM tournament_round_match_list trml
	, match_assignments p1
	, match_assignments p2
	WHERE trml.match_id = p1.match_id
	AND trml.match_id = p2.match_id
	;

-- Create a view, list all players from candidates that have not previously played; therefore best, unmatched player; ranked by score, wins
CREATE OR REPLACE VIEW tournament_player_unmatched AS
	SELECT tmc.tournament_id
	, tmc.player_id
	, tmc.candidate candidate_unmatched
	, ts.score candidate_score
	FROM tournament_match_candidate tmc
		LEFT OUTER JOIN tournament_player_matched tpm
			ON (tmc.tournament_id = tpm.tournament_id
				AND tmc.player_id = tpm.player_id
				AND tmc.candidate = tpm.played_previously)
		LEFT OUTER JOIN tournament_score ts
			ON (tmc.tournament_id = ts.tournament_id
				AND tmc.candidate = ts.player_id)
	AND tpm.played_previously IS NULL
	ORDER BY tmc.tournament_id
	, ts.score DESC 				-- This sort allows Byes to float to the top, score>wins, lower frequency of repeat Byes
	, ts.player_wins DESC 	-- This sort allows Byes to float to the top, score>wins, lower frequency of repeat Byes
	, tmc.candidate
	;

CREATE OR REPLACE VIEW swiss_standings AS
	SELECT trml.tournament_id
	, trml.round_id
	, m.match_id
	, m.match_desc
	, ma1.player_id player1
	, p1.player_name player1_name
	, ma2.player_id player2
	, COALESCE(ma2.player_name,'Bye for round') player2_name
	FROM tournament_round_match_list trml 
	, matches m
	LEFT OUTER JOIN (
		SELECT ma.match_id
		, p.player_id
		, p.player_name
		FROM match_assignments ma
		, players p
		WHERE ma.player_id = p.player_id
		AND ma.match_role_id = 'S'
		) ma2	ON (m.match_id = ma2.match_id)
	, match_assignments ma1
	, players p1
	WHERE trml.match_id = m.match_id
	AND m.match_id = ma1.match_id
	AND ma1.player_id = p1.player_id
	AND ma1.match_role_id IN ('F','B')
	; 