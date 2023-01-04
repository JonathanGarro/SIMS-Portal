SELECT u.id, u.firstname, u.lastname, u.status, u.email, u.job_title, u.slack_id, u.ns_id, u.image_file, ns.ns_name, GROUP_CONCAT(DISTINCT l.name) as languages, GROUP_CONCAT(DISTINCT s.name) as skills, GROUP_CONCAT(DISTINCT p.name) as profiles, COUNT(DISTINCT a.id) as assignment_count 
FROM user u 
JOIN nationalsociety ns ON ns.ns_go_id = u.ns_id 
LEFT JOIN user_language ul ON ul.user_id = u.id 
LEFT JOIN language l ON l.id = ul.language_id 
LEFT JOIN assignment a ON a.user_id = u.id  
LEFT JOIN user_profile up ON up.user_id = u.id 
LEFT JOIN profile p ON p.id = up.profile_id 
LEFT JOIN user_skill us ON us.user_id = u.id 
LEFT JOIN skill s ON s.id = us.skill_id 
WHERE u.status = 'Active'
GROUP BY u.id 
ORDER BY u.firstname