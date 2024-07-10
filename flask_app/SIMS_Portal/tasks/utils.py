from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy.orm import joinedload
from SIMS_Portal.models import User, Task, Log, Emergency
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
    Deletes issues from the database if they no longer exist in the GitHub repository.
    
    Args:
        repo_name (str): The name of the repository to fetch issues from.
    
    Returns:
        list: A list of dictionaries representing the issues that were added, updated, or deleted.
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
        deleted_count = 0
        
        existing_task_ids = set(task.task_id for task in Task.query.filter(Task.repo == repo_name).all())
        github_task_ids = set(issue['number'] for issue in issues)
        
        # Process each issue from GitHub
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
        
        # Delete issues from the database that are no longer on GitHub
        for task_id in existing_task_ids - github_task_ids:
            task_to_delete = Task.query.filter(Task.task_id == task_id).first()
            db.session.delete(task_to_delete)
            deleted_count += 1
            issues_processed.append({
                'task_id': task_to_delete.task_id,
                'repo': task_to_delete.repo,
                'name': task_to_delete.name,
                'state': 'deleted',
                'created_by_gh': task_to_delete.created_by_gh,
                'url': task_to_delete.url,
                'assignees_gh': task_to_delete.assignees_gh,
                'created_at': task_to_delete.created_at
            })
        
        db.session.commit()
        
        log_message = f"[INFO] The get_issues() function ran successfully. New records added: {new_count}. Records updated: {updated_count}. Records deleted: {deleted_count}."
        new_log = Log(message=log_message, user_id=0)
        db.session.add(new_log)
        db.session.commit()
    else:
        log_message = f"[ERROR] The get_issues() function failed. Status code: {response.status_code}. JSON response: {response.json()}. Headers: {response.headers}. URL: {url}"
        new_log = Log(message=log_message, user_id=0)
        db.session.add(new_log)
        db.session.commit()
    
    return issues_processed
    
def refresh_all_active_githubs():
    active_emergencies = db.session.query(Emergency).filter(Emergency.emergency_status == 'Active').all()
    
    for active_emergency in active_emergencies:
        try:
            get_issues(active_emergency.github_repo)
            log_message = f"[INFO] The refresh_all_active_githubs() ran get_issues() and was successful for {active_emergency.emergency_name}"
            new_log = Log(message=log_message, user_id=0)
            db.session.add(new_log)
            db.session.commit()
        except Exception as e:
            log_message = f"[ERROR] The refresh_all_active_githubs() ran get_issues() and failed successful for {active_emergency.emergency_name}: {e}"
            new_log = Log(message=log_message, user_id=0)
            db.session.add(new_log)
            db.session.commit()
    
    return None