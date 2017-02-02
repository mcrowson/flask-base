from flask import abort, flash, redirect, render_template, url_for, request
from flask.ext.login import current_user, login_required

from forms import (ChangeAccountTypeForm, InviteUserForm,
                   NewUserForm)
from . import admin
from ..decorators import admin_required
from ..email import send_email
from ..models import User, EditableHTML, UserHandler


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('administrator/index.html')


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            group=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        user.save()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('administrator/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            group=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        #db.session.add(user)
        #db.session.commit()
        user.save()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        send_email(
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link, )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('administrator/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.list_users()
    return render_template(
        'administrator/registered_users.html', users=users)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(email):
    """View a user's profile."""
    user = UserHandler.get_user(email=email)
    if user is None:
        abort(404)
    return render_template('administrator/manage_user.html', user=user)


@admin.route(
    '/user/<int:email>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(email):
    """Change a user's account type."""
    if current_user.email == email:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('.user_info', email=email))

    user = User.get_user(email)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.group = form.role.data
        user.save()
        flash('Role for user {} successfully changed to {}.'
              .format(user.full_name(), user.group['GroupName']), 'form-success')
    return render_template('administrator/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.get(user_id)
    if user is None:
        abort(404)
    return render_template('administrator/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.get(user_id)
        #db.session.delete(user)
        #db.session.commit()
        user.save()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.get(editor_name)
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    #db.session.add(editor_contents)
    #db.session.commit()
    editor_contents.save()

    return 'OK', 200
