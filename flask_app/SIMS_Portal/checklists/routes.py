from datetime import datetime

from flask import (
	abort, request, render_template, url_for, flash, redirect,
	jsonify, Blueprint
)
from flask_login import (
	current_user, login_required
)

from SIMS_Portal import db
from SIMS_Portal.models import (
	User, Emergency, Checklist, AssignmentChecklist, AssignmentSubTask
)
from SIMS_Portal.main.forms import (
	NewChecklistForm, SubTaskForm, AssignChecklistToEmergencyForm
)


checklists = Blueprint('checklists', __name__)


@checklists.route('/admin/manage_checklist', methods=['GET', 'POST'])
@login_required
def manage_checklist():
    from SIMS_Portal.models import Checklist, Emergency, AssignmentChecklist
    from SIMS_Portal.main.forms import SubTaskForm, AssignChecklistToEmergencyForm
    checklists = Checklist.query.order_by(Checklist.id).all()
    subtask_forms = {cl.id: SubTaskForm(prefix=f'subtask_{cl.id}') for cl in checklists}
    active_emergencies = Emergency.query.filter(Emergency.emergency_status == 'Active').all()
    assign_form = AssignChecklistToEmergencyForm()
    assign_form.emergency_id.choices = [(e.id, e.emergency_name) for e in active_emergencies]
    new_checklist_form = NewChecklistForm()

    # For emergency checklist tab, show assignments for selected emergency
    selected_emergency_id = request.args.get('emergency_id')
    assigned_task_ids = set()
    assigned_subtask_ids = set()
    if selected_emergency_id:
        assignments = AssignmentChecklist.query.filter_by(emergency_id=selected_emergency_id).all()
        assigned_task_ids = {a.checklist_id for a in assignments}
        assigned_subtask_ids = {ast.sub_task_id for a in assignments for ast in a.sub_tasks}
        assign_form.emergency_id.data = int(selected_emergency_id)

    # Add context for task report tab
    emergency_task_stats = {e.id: get_emergency_task_stats(e.id) for e in active_emergencies}

    assigned_tasks = AssignmentChecklist.query.filter_by(emergency_id=selected_emergency_id).all()
    assigned_subtasks = {}
    for task in assigned_tasks:
        for subtask in task.sub_tasks:
            # include who completed the subtask (user id) and name for display
            completed_by_id = getattr(subtask, 'task_completed_by', None)
            completed_by_name = None
            if completed_by_id:
                user = db.session.get(User, completed_by_id)
                completed_by_name = user.fullname if user else None
            assigned_subtasks[subtask.sub_task_id] = {
                'task_completed': subtask.task_completed,
                'task_completed_date': subtask.task_completed_date if subtask.task_completed else None,
                'task_completed_by': completed_by_id,
                'task_completed_by_name': completed_by_name
            }

    return render_template('admin_manage_checklist.html',
        checklists=checklists,
        subtask_forms=subtask_forms,
        active_emergencies=active_emergencies,
        assign_form=assign_form,
        assignment_checklists=[],
        assigned_task_ids=assigned_task_ids,
        assigned_subtask_ids=assigned_subtask_ids,
        active_tab=request.args.get('active_tab', ''),
        new_checklist_form=new_checklist_form,
		assigned_subtasks=assigned_subtasks,
		assigned_tasks=assigned_tasks,
    get_emergency_task_stats=get_emergency_task_stats,
    emergency_task_stats=emergency_task_stats)


@checklists.route('/admin/manage_checklist/add_subtask/<int:checklist_id>', methods=['POST'])
@login_required
def add_subtask(checklist_id):
    from SIMS_Portal.models import SubTask, Checklist, Emergency
    from SIMS_Portal.main.forms import SubTaskForm
    checklists = Checklist.query.order_by(Checklist.id).all()
    subtask_forms = {cl.id: SubTaskForm(prefix=f'subtask_{cl.id}') for cl in checklists}
    active_emergencies = Emergency.query.filter(Emergency.emergency_status == 'Active').all()
    form = SubTaskForm(prefix=f'subtask_{checklist_id}')
    if form.validate_on_submit():
        subtask = SubTask(checklist_id=checklist_id, name=form.name.data, description=form.description.data, task_url=form.task_url.data)
        db.session.add(subtask)
        db.session.commit()
        flash('Sub-task added successfully.', 'success')
        return redirect(url_for('checklists.manage_checklist'))
    else:
        flash('Error adding sub-task. Please check your input.', 'danger')
        subtask_forms[checklist_id] = form
        new_checklist_form = NewChecklistForm()
        return render_template('admin_manage_checklist.html',
                            checklists=checklists,
                            subtask_forms=subtask_forms,
                            active_emergencies=active_emergencies,
                            active_tab=request.args.get('active_tab', ''),
                            new_checklist_form=new_checklist_form,
                            get_emergency_task_stats=get_emergency_task_stats)


@checklists.route('/admin/manage_checklist/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_checklist(id):
    from SIMS_Portal.models import Checklist
    from SIMS_Portal.main.forms import EditChecklistForm
    checklist = db.get_or_404(Checklist, id)
    form = EditChecklistForm(obj=checklist)
    if form.validate_on_submit():
        checklist.task_name = form.task_name.data
        checklist.task_description = form.task_description.data
        checklist.task_url = form.task_url.data
        db.session.commit()
        flash('Checklist updated successfully.', 'success')
        return redirect(url_for('checklists.manage_checklist'))
    return render_template('edit_checklist.html', checklist=checklist, form=form)


# New method to add new checklist
@checklists.route('/admin/manage_checklist/add', methods=['POST'])
@login_required
def add_checklist():
	from SIMS_Portal.models import Checklist
	from SIMS_Portal.main.forms import NewChecklistForm
	form = NewChecklistForm()
	if form.validate_on_submit():
		new_checklist = Checklist(task_name=form.task_name.data, task_description=form.task_description.data, task_url=form.task_url.data)
		db.session.add(new_checklist)
		db.session.commit()
		flash('New checklist added successfully.', 'success')
	else:
		flash('Error adding checklist. Please check your input.', 'danger')
	return redirect(url_for('checklists.manage_checklist'))


@checklists.route('/admin/manage_checklist/remove/<int:id>', methods=['GET', 'POST'])
@login_required
def remove_checklist(id):
    from SIMS_Portal.models import Checklist, AssignmentChecklist
    checklist = db.get_or_404(Checklist, id)

    # Prevent deletion if this checklist is assigned to any emergency assignments
    assignment_count = AssignmentChecklist.query.filter_by(checklist_id=id).count()
    if assignment_count and assignment_count > 0:
        flash(f'Cannot delete checklist "{checklist.task_name}" because it is assigned to {assignment_count} assignment(s).', 'danger')
        return redirect(url_for('checklists.manage_checklist'))

    db.session.delete(checklist)
    db.session.commit()
    flash('Checklist removed successfully.', 'success')
    return redirect(url_for('checklists.manage_checklist'))


# SubTask CRUD
@checklists.route('/admin/manage_checklist/edit_subtask/<int:subtask_id>', methods=['GET', 'POST'])
@login_required
def edit_subtask(subtask_id):
    from SIMS_Portal.models import SubTask
    from SIMS_Portal.main.forms import EditSubTaskForm
    subtask = db.get_or_404(SubTask, subtask_id)
    form = EditSubTaskForm(obj=subtask)
    if form.validate_on_submit():
        subtask.name = form.name.data
        subtask.description = form.description.data
        subtask.task_url = form.task_url.data
        db.session.commit()
        flash('Sub-task updated successfully.', 'success')
        return redirect(url_for('checklists.manage_checklist'))
    return render_template('edit_subtask.html', subtask=subtask, form=form)


@checklists.route('/admin/manage_checklist/remove_subtask/<int:subtask_id>', methods=['GET', 'POST'])
@login_required
def remove_subtask(subtask_id):
    from SIMS_Portal.models import SubTask, AssignmentSubTask
    subtask = db.get_or_404(SubTask, subtask_id)

    # Prevent deletion if this subtask is used in any assignment
    assigned_count = AssignmentSubTask.query.filter_by(sub_task_id=subtask_id).count()
    if assigned_count and assigned_count > 0:
        flash(f'Cannot delete sub-task "{subtask.name}" because it is assigned to {assigned_count} assignment(s).', 'danger')
        return redirect(url_for('checklists.manage_checklist'))

    db.session.delete(subtask)
    db.session.commit()
    flash('Sub-task removed successfully.', 'success')
    return redirect(url_for('checklists.manage_checklist'))


# Emergency Checklist Assignment
@checklists.route('/admin/manage_checklist/assign_to_emergency', methods=['POST'])
@login_required
def assign_checklist_to_emergency():
    from SIMS_Portal.models import AssignmentChecklist, AssignmentSubTask, Emergency, Checklist
    from SIMS_Portal.main.forms import AssignChecklistToEmergencyForm
    form = AssignChecklistToEmergencyForm()
    # Populate emergency choices
    emergencies = Emergency.query.filter(Emergency.emergency_status == 'Active').all()
    form.emergency_id.choices = [(e.id, e.emergency_name) for e in emergencies]
    if form.validate_on_submit():
        emergency_id = form.emergency_id.data
        selected_tasks = request.form.getlist('tasks')
        for checklist_id in selected_tasks:
            ac = AssignmentChecklist(emergency_id=emergency_id, checklist_id=checklist_id, task_completed=False)
            db.session.add(ac)
            db.session.flush()
            subtask_ids = request.form.getlist(f'subtasks_{checklist_id}')
            for subtask_id in subtask_ids:
                ast = AssignmentSubTask(assignment_checklist_id=ac.id, sub_task_id=subtask_id, task_completed=False)
                db.session.add(ast)
        db.session.commit()
        flash('Checklist and sub-tasks assigned to emergency.', 'success')
        return redirect(url_for('checklists.manage_checklist', active_tab='emergency-checklist'))
    # If not valid, re-render the page with errors
    checklists = Checklist.query.order_by(Checklist.id).all()
    subtask_forms = {cl.id: SubTaskForm(prefix=f'subtask_{cl.id}') for cl in checklists}
    active_emergencies = emergencies
    new_checklist_form = NewChecklistForm()
    return render_template('admin_manage_checklist.html',
                         checklists=checklists,
                         subtask_forms=subtask_forms,
                         active_emergencies=active_emergencies,
                         assign_form=form,
                         active_tab='emergency-checklist',
                         new_checklist_form=new_checklist_form,
                         get_emergency_task_stats=get_emergency_task_stats)


@checklists.route('/admin/manage_checklist/edit_assigned_checklist/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def edit_assigned_checklist(assignment_id):
    from SIMS_Portal.models import AssignmentChecklist
    from SIMS_Portal.main.forms import EditChecklistForm
    assignment = db.get_or_404(AssignmentChecklist, assignment_id)
    checklist = assignment.checklist
    form = EditChecklistForm(obj=checklist)
    if form.validate_on_submit():
        checklist.task_name = form.task_name.data
        checklist.task_description = form.task_description.data
        checklist.task_url = form.task_url.data
        db.session.commit()
        flash('Assigned checklist updated successfully.', 'success')
        return redirect(url_for('checklists.manage_checklist', active_tab='emergency-checklist'))
    return render_template('edit_checklist.html', checklist=checklist, form=form)


@checklists.route('/admin/manage_checklist/delete_assigned_checklist/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def delete_assigned_checklist(assignment_id):
    from SIMS_Portal.models import AssignmentChecklist, AssignmentSubTask
    assignment = db.get_or_404(AssignmentChecklist, assignment_id)
    # Delete all related AssignmentSubTasks first
    AssignmentSubTask.query.filter_by(assignment_checklist_id=assignment.id).delete()
    db.session.delete(assignment)
    db.session.commit()
    flash('Assigned checklist deleted successfully.', 'success')
    return redirect(url_for('checklists.manage_checklist', active_tab='emergency-checklist'))


@checklists.route('/admin/manage_checklist/edit_assigned_subtask/<int:assigned_subtask_id>', methods=['GET', 'POST'])
@login_required
def edit_assigned_subtask(assigned_subtask_id):
    from SIMS_Portal.models import AssignmentSubTask
    from SIMS_Portal.main.forms import EditSubTaskForm
    assigned_subtask = db.get_or_404(AssignmentSubTask, assigned_subtask_id)
    subtask = assigned_subtask.sub_task
    form = EditSubTaskForm(obj=subtask)
    if form.validate_on_submit():
        subtask.name = form.name.data
        subtask.description = form.description.data
        subtask.task_url = form.task_url.data
        db.session.commit()
        flash('Assigned sub-task updated successfully.', 'success')
        return redirect(url_for('checklists.manage_checklist', active_tab='emergency-checklist'))
    return render_template('edit_subtask.html', subtask=subtask, form=form)


@checklists.route('/admin/manage_checklist/delete_assigned_subtask/<int:assigned_subtask_id>', methods=['GET', 'POST'])
@login_required
def delete_assigned_subtask(assigned_subtask_id):
    from SIMS_Portal.models import AssignmentSubTask
    assigned_subtask = db.get_or_404(AssignmentSubTask, assigned_subtask_id)
    db.session.delete(assigned_subtask)
    db.session.commit()
    flash('Assigned sub-task deleted successfully.', 'success')
    return redirect(url_for('checklists.manage_checklist', active_tab='emergency-checklist'))


@checklists.route('/admin/manage_checklist/update_task_status/<int:assignment_id>', methods=['POST'])
@login_required
def update_task_status(assignment_id):
    assignment_subtask = db.get_or_404(AssignmentSubTask, assignment_id)
    if request.method == 'POST':
        assignment_subtask.task_completed = True
        assignment_subtask.task_completed_date = datetime.utcnow()
        assignment_subtask.task_completed_by = current_user.id  # Set the user who completed the task
        db.session.commit()
        return jsonify({'success': True})
    """Update the completion status and date of a task"""
    if not current_user.is_admin:
        abort(403)

    from SIMS_Portal.models import AssignmentChecklist
    assignment = db.get_or_404(AssignmentChecklist, assignment_id)

    completed_date = request.form.get('completed_date')
    if completed_date:
        assignment.task_completed = True
        assignment.task_completed_date = datetime.strptime(completed_date, '%Y-%m-%dT%H:%M')
    else:
        assignment.task_completed = False
        assignment.task_completed_date = None

    db.session.commit()
    flash('Task status updated successfully', 'success')
    return redirect(url_for('checklists.update_emergency_checklist', emergency_id=assignment.emergency_id))


def get_emergency_task_stats(emergency_id):
    """Get task statistics for an emergency"""
    from SIMS_Portal.models import AssignmentChecklist, AssignmentSubTask
    # Get all assignments (checklists) for this emergency
    assignments = AssignmentChecklist.query.filter_by(emergency_id=emergency_id).all()

    # Count main tasks (checklists)
    total_tasks = len(assignments)

    # Aggregate across assignments
    total_subtasks = 0
    completed_subtasks = 0
    all_completed_dates = []
    assignments_data = []

    # Lazy import of models used below
    from SIMS_Portal.models import Checklist, SubTask, User

    for ac in assignments:
        checklist = getattr(ac, 'checklist', None)
        if checklist is None and getattr(ac, 'checklist_id', None):
            checklist = db.session.get(Checklist, ac.checklist_id)

        checklist_name = getattr(checklist, 'task_name', None) or getattr(checklist, 'name', 'Checklist')

        # Use the AssignmentSubTask rows related to this assignment
        ast_rows = getattr(ac, 'sub_tasks', []) or AssignmentSubTask.query.filter_by(assignment_checklist_id=ac.id).all()

        assignment_total_subtasks = len(ast_rows)
        assignment_completed = 0
        subtasks_list = []

        for ast in ast_rows:
            # Resolve the SubTask entity
            sub = getattr(ast, 'sub_task', None)
            if sub is None and getattr(ast, 'sub_task_id', None):
                sub = db.session.get(SubTask, ast.sub_task_id)

            sub_name = getattr(sub, 'name', '') if sub is not None else ''

            completed = bool(getattr(ast, 'task_completed', False))
            completed_date = getattr(ast, 'task_completed_date', None)
            completed_by_id = getattr(ast, 'task_completed_by', None) or getattr(ast, 'completed_by', None)
            completed_by_name = None
            if completed_by_id:
                try:
                    user = db.session.get(User, completed_by_id)
                    if user:
                        completed_by_name = f"{getattr(user, 'firstname', '')} {getattr(user, 'lastname', '')}".strip()
                except Exception:
                    completed_by_name = None

            if completed:
                assignment_completed += 1
                completed_subtasks += 1
                if completed_date:
                    all_completed_dates.append(completed_date)

            subtasks_list.append({
                'id': getattr(sub, 'id', None) or getattr(ast, 'sub_task_id', None),
                'name': sub_name,
                'completed': completed,
                'completed_by': completed_by_id,
                'completed_by_name': completed_by_name,
                'completed_date': completed_date
            })

        total_subtasks += assignment_total_subtasks

        assignment_completion_rate = round((assignment_completed / assignment_total_subtasks * 100) if assignment_total_subtasks > 0 else 0)

        assignments_data.append({
            'assignment_id': getattr(ac, 'id', None),
            'checklist_id': getattr(checklist, 'id', None) if checklist is not None else getattr(ac, 'checklist_id', None),
            'checklist_name': checklist_name,
            'total_subtasks': assignment_total_subtasks,
            'completed_subtasks': assignment_completed,
            'completion_rate': assignment_completion_rate,
            'subtasks': subtasks_list
        })

    completion_rate = round((completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0)

    last_update = None
    if all_completed_dates:
        try:
            last_dt = max(all_completed_dates)
            last_update = last_dt.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_dt, 'strftime') else str(last_dt)
        except Exception:
            last_update = str(max(all_completed_dates))

    return {
        'total_tasks': total_tasks,
        'total_subtasks': total_subtasks,
        'completed_tasks': completed_subtasks,
        'completion_rate': completion_rate,
        'last_update': last_update,
        'assignments': assignments_data
    }


@checklists.route('/admin/manage_checklist/unmark_subtask/<int:subtask_id>/<int:emergency_id>', methods=['POST'])
@login_required
def unmark_subtask(subtask_id, emergency_id):
    """Unmark a subtask as completed for an emergency.

    The frontend sends the SubTask.id (sub_task_id) and emergency_id. We locate the
    corresponding AssignmentSubTask by joining to AssignmentChecklist filtered by
    the emergency, then clear completion fields.
    """
    # only admins may unmark via this admin endpoint
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        # find the specific AssignmentSubTask for this emergency and subtask
        assigned_subtask = AssignmentSubTask.query.join(AssignmentChecklist).filter(
            AssignmentChecklist.emergency_id == emergency_id,
            AssignmentSubTask.sub_task_id == subtask_id
        ).first()

        if not assigned_subtask:
            return jsonify({'success': False, 'message': 'Subtask not found'}), 404

        assigned_subtask.task_completed = False
        assigned_subtask.task_completed_date = None
        assigned_subtask.task_completed_by = None
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@checklists.route('/admin/manage_checklist/override_subtask_date/<int:subtask_id>/<int:emergency_id>', methods=['POST'])
@login_required
def override_subtask_date(subtask_id, emergency_id):
    """Override the completion date of a subtask"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        data = request.get_json() or {}
        new_date_str = data.get('new_date')
        if not new_date_str:
            return jsonify({'success': False, 'message': 'No new_date provided'}), 400

        # parse the datetime-local format coming from browser (e.g. 2025-09-20T14:30)
        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            # try ISO format fallback
            new_date = datetime.fromisoformat(new_date_str)

        # find the AssignmentSubTask that belongs to the given emergency and subtask
        assigned_subtask = AssignmentSubTask.query.join(AssignmentChecklist).filter(
            AssignmentChecklist.emergency_id == emergency_id,
            AssignmentSubTask.sub_task_id == subtask_id
        ).first()

        if not assigned_subtask:
            return jsonify({'success': False, 'message': 'Subtask not found'}), 404

        assigned_subtask.task_completed = True
        assigned_subtask.task_completed_date = new_date
        assigned_subtask.task_completed_by = current_user.id
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@checklists.route('/admin/manage_checklist/update_emergency_checklist', methods=['POST', 'GET'])
@login_required
def update_emergency_checklist():
    if not current_user.is_admin:
        abort(403)

    assign_form = AssignChecklistToEmergencyForm()
    active_emergencies = Emergency.query.filter_by(emergency_status='Active').all()
    assign_form.emergency_id.choices = [(e.id, e.emergency_name) for e in active_emergencies]
    checklists = Checklist.query.all()

    if request.method == 'GET':
        emergency_id = request.args.get('emergency_id', type=int)
        if emergency_id:
            # Set the selected emergency in the form
            assign_form.emergency_id.data = emergency_id
            assigned_tasks = AssignmentChecklist.query.filter_by(emergency_id=emergency_id).all()
            assigned_subtasks = {}

            for task in assigned_tasks:
                for subtask in task.sub_tasks:
                    completed_by_id = getattr(subtask, 'task_completed_by', None)
                    completed_by_name = None
                    if completed_by_id:
                        user = db.session.get(User, completed_by_id)
                        completed_by_name = user.fullname if user else None
                    assigned_subtasks[subtask.sub_task_id] = {
                        'task_completed': subtask.task_completed,
                        'task_completed_date': subtask.task_completed_date,
                        'task_completed_by': completed_by_id,
                        'task_completed_by_name': completed_by_name
                    }

            return render_template(
                'admin_manage_checklist.html',
                assign_form=assign_form,
                active_emergencies=active_emergencies,
                checklists=checklists,
                active_tab='emergency-checklist',
                assigned_subtasks=assigned_subtasks,
                assigned_task_ids=[task.checklist_id for task in assigned_tasks],
                assigned_subtask_ids=list(assigned_subtasks.keys()),
                get_emergency_task_stats=get_emergency_task_stats,
                new_checklist_form=NewChecklistForm(),
                subtask_forms={cl.id: SubTaskForm(prefix=f'subtask_{cl.id}') for cl in checklists}
            )

    elif request.method == 'POST':
        emergency_id = request.form.get('emergency_id', type=int)
        if not emergency_id:
            flash('No emergency selected', 'danger')
            return redirect(url_for('checklists.manage_checklist'))

        try:
            # Get existing assignments to preserve completion status
            existing_assignments = AssignmentChecklist.query.filter_by(emergency_id=emergency_id).all()
            existing_subtasks = {}

            # Create a lookup for existing subtasks to preserve their status
            for assignment in existing_assignments:
                for subtask in assignment.sub_tasks:
                    key = (subtask.sub_task_id, emergency_id)
                    existing_subtasks[key] = {
                        'task_completed': subtask.task_completed,
                        'task_completed_date': subtask.task_completed_date if subtask.task_completed else None
                    }

            # Robustly parse submitted tasks and subtasks from the form. The template may submit
            # subtasks as 'subtasks_<parent_id>' or as an array 'subtask_ids[]' containing
            # values like '<parent>_<subtask>' or just subtask ids. Normalize into two structures:
            # - tasks: set of parent checklist ids (strings)
            # - task_subtasks: dict[parent_id] -> set(subtask_ids)
            tasks = set(request.form.getlist('tasks'))
            task_subtasks = {}

            # Handle keys like 'subtasks_<parent_id>' which contain subtask ids
            for key in request.form.keys():
                if key.startswith('subtasks_'):
                    try:
                        parent_id = int(key.split('_', 1)[1])
                    except Exception:
                        continue
                    values = request.form.getlist(key)
                    for v in values:
                        try:
                            sid = int(v)
                        except Exception:
                            continue
                        task_subtasks.setdefault(parent_id, set()).add(sid)
                        tasks.add(str(parent_id))

            # Handle older or alternate input name 'subtask_ids[]' or 'subtask_ids'
            subtask_list_values = request.form.getlist('subtask_ids[]') or request.form.getlist('subtask_ids')
            if subtask_list_values:
                for val in subtask_list_values:
                    if not val:
                        continue
                    if '_' in val:
                        try:
                            parent_id, sid = map(int, val.split('_'))
                        except Exception:
                            continue
                        task_subtasks.setdefault(parent_id, set()).add(sid)
                        tasks.add(str(parent_id))
                    else:
                        # If only a subtask id is provided, lookup its parent checklist
                        try:
                            sid = int(val)
                        except Exception:
                            continue
                        try:
                            from SIMS_Portal.models import SubTask
                            sub = db.session.get(SubTask, sid)
                            if sub:
                                task_subtasks.setdefault(sub.checklist_id, set()).add(sid)
                                tasks.add(str(sub.checklist_id))
                        except Exception:
                            continue

            # Keep a map of task assignments we will retain or create
            task_assignments = {}

            # Process existing assignments: if parent task is no longer selected, do NOT delete
            # completed subtasks. Only delete the entire assignment if it contains no completed subtasks
            # and is not selected.
            for existing_assignment in existing_assignments:
                checklist_id_str = str(existing_assignment.checklist_id)
                if checklist_id_str not in tasks:
                    # Parent not selected in the submitted form
                    has_completed = any(st.task_completed for st in existing_assignment.sub_tasks)
                    if has_completed:
                        # Remove only uncompleted subtasks
                        for st in list(existing_assignment.sub_tasks):
                            if not st.task_completed:
                                db.session.delete(st)
                        # retain the assignment to preserve completed subtasks
                        task_assignments[existing_assignment.checklist_id] = existing_assignment
                    else:
                        # Safe to remove assignment and any subtasks
                        AssignmentSubTask.query.filter_by(assignment_checklist_id=existing_assignment.id).delete()
                        db.session.delete(existing_assignment)
                else:
                    # Parent selected: keep the assignment for further processing
                    task_assignments[existing_assignment.checklist_id] = existing_assignment

            # Now ensure tasks that need to be created exist, and synchronize subtasks
            for task_id_str in list(tasks):
                try:
                    task_id = int(task_id_str)
                except Exception:
                    continue
                if task_id not in task_assignments:
                    # Create new task assignment only if it doesn't exist
                    new_task = AssignmentChecklist(
                        emergency_id=emergency_id,
                        checklist_id=task_id,
                        task_completed=False
                    )
                    db.session.add(new_task)
                    db.session.flush()
                    task_assignments[task_id] = new_task

                task = task_assignments[task_id]

                # Current subtask ids for this task assignment
                current_subtask_ids = set(st.sub_task_id for st in task.sub_tasks)
                selected_subtask_ids = set(task_subtasks.get(task_id, []))

                # Remove subtasks that are no longer selected, unless they are completed
                for subtask in list(task.sub_tasks):
                    if subtask.sub_task_id not in selected_subtask_ids and not subtask.task_completed:
                        db.session.delete(subtask)

                # Add new subtasks that are selected
                if selected_subtask_ids:
                    for subtask_id in selected_subtask_ids:
                        if subtask_id not in current_subtask_ids:
                            new_subtask = AssignmentSubTask(
                                assignment_checklist_id=task.id,
                                sub_task_id=subtask_id,
                                task_completed=False
                            )
                            # Restore completion state if we have it from existing records
                            key = (subtask_id, emergency_id)
                            if key in existing_subtasks:
                                new_subtask.task_completed = existing_subtasks[key].get('task_completed', False)
                                new_subtask.task_completed_date = existing_subtasks[key].get('task_completed_date')

                            db.session.add(new_subtask)

            try:
                db.session.commit()
                flash('Emergency checklist updated successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating checklist: {str(e)}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating emergency checklist: {str(e)}', 'danger')

        return redirect(url_for('checklists.update_emergency_checklist', emergency_id=emergency_id))

    return render_template(
        'admin_manage_checklist.html',
        assign_form=assign_form,
        active_emergencies=active_emergencies,
        checklists=checklists,
        active_tab='emergency-checklist',
        new_checklist_form=NewChecklistForm(),
        subtask_forms={cl.id: SubTaskForm(prefix=f'subtask_{cl.id}') for cl in checklists},
        get_emergency_task_stats=get_emergency_task_stats
    )
