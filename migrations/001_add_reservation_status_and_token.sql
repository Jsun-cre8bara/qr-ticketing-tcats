CREATE TYPE reservation_status AS ENUM (
  'pending',
  'reserved_unassigned',
  'reserved_assigned',
  'issued',
  'checked_in',
  'cancelled',
  'expired'
);

ALTER TABLE reservations
  ADD COLUMN status reservation_status NOT NULL DEFAULT 'reserved_unassigned',
  ADD COLUMN token VARCHAR(16),
  ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE UNIQUE INDEX IF NOT EXISTS ux_reservations_token
  ON reservations(token)
  WHERE token IS NOT NULL;