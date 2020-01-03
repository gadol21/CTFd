from flask import current_app as app, render_template, request, redirect, jsonify, url_for, Blueprint
from CTFd.utils.user import is_admin
from CTFd.utils.decorators import admins_only
from CTFd.cache import cache
from CTFd.models import db
from .models import Containers

from . import utils

def load(app):
    app.db.create_all()
    admin_containers = Blueprint('admin_containers', __name__, template_folder='templates')

    @admin_containers.route('/admin/containers', methods=['GET'])
    @admins_only
    def list_container():
        containers = Containers.query.all()
        for c in containers:
            c.status = utils.container_status(c.name)
            c.ports = ', '.join(utils.container_ports(c.name, verbose=True))
        return render_template('containers.html', containers=containers)


    @admin_containers.route('/admin/containers/<int:container_id>/stop', methods=['POST'])
    @admins_only
    def stop_container(container_id):
        container = Containers.query.filter_by(id=container_id).first_or_404()
        utils.container_stop(container.name)
        # FIXME: Indicate success/failure
        return redirect(url_for('admin_containers.list_container'))


    @admin_containers.route('/admin/containers/<int:container_id>/start', methods=['POST'])
    @admins_only
    def run_container(container_id):
        container = Containers.query.filter_by(id=container_id).first_or_404()
        if utils.container_status(container.name) == 'missing':
            utils.run_image(container.name)
        else:
            utils.container_start(container.name)
        # FIXME: Indicate success/failure
        return redirect(url_for('admin_containers.list_container'))

    # NOTE: Almost the same as new_container
    @admin_containers.route('/admin/containers/<int:container_id>/rebuild', methods=['POST'])
    @admins_only
    def rebuild_container(container_id):
        container = Containers.query.filter_by(id=container_id).first_or_404()
        name = container.name
        utils.create_image(name=name, add_to_db=False)
        utils.run_image(name)
        return redirect(url_for('admin_containers.list_container'))


    @admin_containers.route('/admin/containers/<int:container_id>/delete', methods=['POST'])
    def delete_container(container_id):
        container = Containers.query.filter_by(id=container_id).first_or_404()
        if utils.delete_image(container.name):
            db.session.delete(container)
            db.session.commit()
            db.session.close()
        # FIXME: Indicate success/failure
        return redirect(url_for('admin_containers.list_container'))


    @admin_containers.route('/admin/containers/new', methods=['POST'])
    @admins_only
    def new_container():
        name = request.form.get('name')
        if not set(name) <= set('abcdefghijklmnopqrstuvwxyz0123456789-_'):
            #return redirect(url_for('admin_containers.list_container'))
            return 'Name must be lowercase!'
        utils.create_image(name=name)
        utils.run_image(name)
        return redirect(url_for('admin_containers.list_container'))

    app.register_blueprint(admin_containers)