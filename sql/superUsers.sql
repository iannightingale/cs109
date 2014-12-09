-- Add to super users 
INSERT INTO super_users (user_id) (SELECT user_id FROM ratings WHERE user_rating > 0 
GROUP BY user_id HAVING count(user_id) >= 1000) ON DUPLICATE KEY UPDATE timestamp = CURRENT_TIMESTAMP;