# Database Schema

## Core tables

users
affiliations
samples
sample_affiliations
sample_species
genomic_records
audit_log

## Key rule

Each ingested sample automatically receives
a provisional species entry:
species_name = "unidentified"

