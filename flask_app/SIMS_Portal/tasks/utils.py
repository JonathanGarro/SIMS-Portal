from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from SIMS_Portal.models import User, Task, Log
from datetime import datetime
import os
import requests
import logging

def get_repos():
    org = "Surge-Information-Management-Support"
    url = f"https://api.github.com/orgs/{org}/repos"
    
    repos = []
    page = 1
    
    while True:
        response = requests.get(url, params={'page': page, 'per_page': 100})
        if response.status_code != 200:
            print(f"Failed to retrieve data: {response.status_code}")
            break
        
        data = response.json()
        if not data:
            break
        
        repos.extend(data)
        page += 1
    
    return repos

def get_issues(repo_name):
    """
    Fetches issues from the specified SIMS GitHub repository and updates or inserts them into the database.
    
    Retrieves all issues (both open and closed) from the specified GitHub repository 
    within the 'Surge-Information-Management-Support' organization. It then checks if each issue 
    already exists in the database based on the GitHub issue ID (task_id). If an issue does not exist, 
    it inserts a new record. If the issue exists, it updates the record if any fields have changed.
    
    Args:
        repo_name (str): The name of the repository to fetch issues from.
    
    Returns:
        list: A list of dictionaries representing the issues that were added or updated.
    """
    
    ACCESS_TOKEN = os.environ.get('GITHUB_TOKEN')
    ORGANIZATION = 'Surge-Information-Management-Support'
    REPO = repo_name
    
    headers = {
        'Authorization': f'token {ACCESS_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{ORGANIZATION}/{REPO}/issues?state=all'
    
    response = requests.get(url, headers=headers)
    
    issues_processed = []
    
    if response.status_code == 200:
        issues = response.json()
        new_count = 0
        updated_count = 0
        for issue in issues:
            task = Task.query.filter(Task.task_id == issue['number']).first()
            if task is None:
                task = Task(
                    task_id=issue['number'],
                    repo=repo_name,
                    name=issue['title'],
                    state=issue['state'],
                    created_by_gh=issue['user']['login'],
                    url=issue['html_url'],
                    assignees_gh=','.join([assignee['login'] for assignee in issue['assignees']]),
                    created_at=datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                )
                db.session.add(task)
                new_count += 1
                issues_processed.append({
                    'task_id': task.task_id,
                    'repo': task.repo,
                    'name': task.name,
                    'state': task.state,
                    'created_by_gh': task.created_by_gh,
                    'url': task.url,
                    'assignees_gh': task.assignees_gh,
                    'created_at': task.created_at
                })
            else:
                fields_to_check = {
                    'repo': repo_name,
                    'name': issue['title'],
                    'state': issue['state'],
                    'created_by_gh': issue['user']['login'],
                    'url': issue['html_url'],
                    'assignees_gh': ','.join([assignee['login'] for assignee in issue['assignees']]),
                    'created_at': datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                }
                
                updated = False
                for field, new_value in fields_to_check.items():
                    if getattr(task, field) != new_value:
                        setattr(task, field, new_value)
                        updated = True
                
                if updated:
                    task.date_modified = datetime.utcnow()
                    updated_count += 1
                    issues_processed.append({
                        'task_id': task.task_id,
                        'repo': task.repo,
                        'name': task.name,
                        'state': task.state,
                        'created_by_gh': task.created_by_gh,
                        'url': task.url,
                        'assignees_gh': task.assignees_gh,
                        'created_at': task.created_at,
                        'date_modified': task.date_modified
                    })
        
        db.session.commit()
        
        log_message = f"[INFO] The get_issues() function ran successfully. New records added: {new_count}. Records updated: {updated_count}."
        new_log = Log(message=log_message, user_id=0)
        db.session.add(new_log)
        db.session.commit()
    else:
        log_message = f"[ERROR] The get_issues() function failed. Status code: {response.status_code}. JSON response: {response.json()}. Headers: {response.headers}. URL: {url}"
        new_log = Log(message=log_message, user_id=0)
        db.session.add(new_log)
        db.session.commit()
    
    return issues_processed