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

CREATE OR REPLACE VIEW tournament_score AS
	SELECT trml.tournament_id
	, ma.player_id
	, COALESCE(SUM(mrt.match_result_modifier),0) score
	, COALESCE(SUM(CASE WHEN ma.match_result_id = 'W' then 1 else 0 end),0) player_wins
	, COALESCE(SUM(CASE WHEN ma.match_result_id IS NOT NULL then 1 else 0 end),0) matches_played
	FROM match_assignments ma
	, match_result_types mrt
	, tournament_round_match_list trml
	WHERE ma.match_id = trml.match_id
	AND ma.match_result_id = mrt.match_result_id
	GROUP BY trml.tournament_id
	, ma.player_id
	ORDER BY trml.tournament_id
	, SUM(mrt.match_result_modifier) DESC
	;

CREATE OR REPLACE VIEW tournament_round_players_assigned AS
	SELECT trml.round_id
	, tr.player_id
	FROM tournament_registrants tr
	, tournament_round_match_list trml
	, match_assignments ma
	WHERE tr.tournament_id = trml.tournament_id
	AND trml.match_id = ma.match_id
	;

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
	, ts.score DESC
	, tr.player_id
	;

CREATE OR REPLACE VIEW tournament_match_candidate AS
	SELECT tr.tournament_id 
	, tr.player_id
	, tr2.player_id candidate
	FROM tournament_registrants tr
	, tournament_registrants tr2
	WHERE tr.tournament_id = tr2.tournament_id
	AND tr.player_id <> tr2.player_id
	;

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
		, ts.score DESC
		, tmc.candidate
		;