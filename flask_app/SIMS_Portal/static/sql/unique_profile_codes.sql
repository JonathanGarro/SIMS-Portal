SELECT user_id, profile_id, tier, name, user_id || profile_id || tier as unique_code 
FROM user_profile 
JOIN profile ON profile.id = user_profile.profile_id
WHERE user_id = 1