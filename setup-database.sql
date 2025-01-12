CREATE TABLE IF NOT EXISTS relay (
  pin REAL,
  state INTEGER
);

CREATE TABLE IF NOT EXISTS regulator (
  target_temperature REAL
);

INSERT INTO regulator (target_temperature) values (5.2);
