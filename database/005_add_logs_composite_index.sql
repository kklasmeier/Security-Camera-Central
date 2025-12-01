-- Migration: Add composite index for logs date range queries
-- File: 005_add_logs_composite_index.sql
-- 
-- The main query pattern is:
--   WHERE level IN (...) AND source = X AND timestamp BETWEEN ... ORDER BY id DESC LIMIT N
--
-- Adding a composite index on (level, source, timestamp) to optimize this pattern.
-- The existing idx_source_timestamp helps when filtering by source first,
-- but this index helps when level filtering is the primary discriminator.

-- Add composite index for level + source + timestamp queries
CREATE INDEX idx_level_source_timestamp ON logs (level, source, timestamp);

-- Verify indexes
-- SHOW INDEX FROM logs;