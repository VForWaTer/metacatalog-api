-- create the table containing API keys.
CREATE TABLE IF NOT EXISTS user_access_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    token_hash CHARACTER VARYING (64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    valid_until TIMESTAMP,
    CONSTRAINT persons_access_token
        FOREIGN KEY (user_id) REFERENCES persons (id) 
        ON UPDATE CASCADE ON DELETE CASCADE
);