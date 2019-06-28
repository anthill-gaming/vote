#!/usr/bin/env bash


# Setup postgres database
createuser -d anthill_vote -U postgres
createdb -U anthill_vote anthill_vote
