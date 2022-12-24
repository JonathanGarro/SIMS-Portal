SELECT user_id, firstname || ' ' || lastname as user_name, profile_id, max(tier) as max_tier, user_id || profile_id as unique_code, name 
FROM user_profile 
JOIN profile 
ON profile.id = user_profile.profile_id 
JOIN user ON user.id = user_profile.user_id 
GROUP BY user_id, profile_id