SELECT firstname, lastname, b.id, b.name, b.badge_url FROM user 
JOIN user_badge 
ON user_badge.user_id = user.id 
JOIN badge b ON b.id = user_badge.badge_id 
WHERE user.id = 1 
ORDER BY name