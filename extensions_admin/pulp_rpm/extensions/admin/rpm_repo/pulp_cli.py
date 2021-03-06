import os
from gettext import gettext as _

from pulp.client.commands.repo import cudl, sync_publish, upload
from pulp.client.commands.repo.query import RepoSearchCommand
from pulp.client.commands.repo.status import PublishStepStatusRenderer
from pulp.client.upload import manager as upload_lib

from pulp_rpm.common import constants, ids
from pulp_rpm.extensions.admin import structure
from pulp_rpm.extensions.admin.upload import package
from pulp_rpm.extensions.admin import (contents, copy_commands, export, remove, repo_create_update,
                                       repo_list, status, sync_schedules)
from pulp_rpm.extensions.admin.upload import (category, comps, errata)
from pulp_rpm.extensions.admin.upload import group as package_group


DESC_EXPORT_STATUS = _('displays the status of a running ISO export of a repository')
RPM_UPLOAD_SUBDIR = 'rpm'


def initialize(context):
    structure.ensure_repo_structure(context.cli)
    upload_manager = _upload_manager(context)

    repo_section = structure.repo_section(context.cli)
    repo_section.add_command(repo_create_update.RpmRepoCreateCommand(context))
    repo_section.add_command(repo_create_update.RpmRepoUpdateCommand(context))
    repo_section.add_command(cudl.DeleteRepositoryCommand(context))
    repo_section.add_command(repo_list.RpmRepoListCommand(context))
    repo_section.add_command(RepoSearchCommand(context, constants.REPO_NOTE_RPM))

    copy_section = structure.repo_copy_section(context.cli)
    copy_section.add_command(copy_commands.RpmCopyCommand(context))
    copy_section.add_command(copy_commands.ErrataCopyCommand(context))
    copy_section.add_command(copy_commands.DistributionCopyCommand(context))
    copy_section.add_command(copy_commands.PackageGroupCopyCommand(context))
    copy_section.add_command(copy_commands.PackageCategoryCopyCommand(context))
    copy_section.add_command(copy_commands.PackageEnvironmentCopyCommand(context))
    copy_section.add_command(copy_commands.AllCopyCommand(context))
    copy_section.add_command(copy_commands.SrpmCopyCommand(context))

    # Disabled as per 950690. We'll likely be able to add these back once the new
    # yum importer is finished and DRPMs are properly handled.
    # copy_section.add_command(copy_commands.DrpmCopyCommand(context))

    remove_section = structure.repo_remove_section(context.cli)
    remove_section.add_command(remove.RpmRemoveCommand(context))
    remove_section.add_command(remove.SrpmRemoveCommand(context))
    remove_section.add_command(remove.DrpmRemoveCommand(context))
    remove_section.add_command(remove.ErrataRemoveCommand(context))
    remove_section.add_command(remove.PackageGroupRemoveCommand(context))
    remove_section.add_command(remove.PackageCategoryRemoveCommand(context))
    remove_section.add_command(remove.PackageEnvironmentRemoveCommand(context))
    remove_section.add_command(remove.DistributionRemoveCommand(context))

    contents_section = structure.repo_contents_section(context.cli)
    contents_section.add_command(contents.SearchRpmsCommand(context))
    contents_section.add_command(contents.SearchDrpmsCommand(context))
    contents_section.add_command(contents.SearchSrpmsCommand(context))
    contents_section.add_command(contents.SearchPackageGroupsCommand(context))
    contents_section.add_command(contents.SearchPackageCategoriesCommand(context))
    contents_section.add_command(contents.SearchPackageEnvironmentsCommand(context))
    contents_section.add_command(contents.SearchDistributionsCommand(context))
    contents_section.add_command(contents.SearchErrataCommand(context))

    # Add the group section, all its subsections, and commands
    group_export_section = structure.repo_group_export_section(context.cli)
    renderer = PublishStepStatusRenderer(context)
    group_export_section.add_command(export.RpmGroupExportCommand(context, renderer))
    group_export_section.add_command(export.GroupExportStatusCommand(context, renderer))

    uploads_section = structure.repo_uploads_section(context.cli)
    uploads_section.add_command(package.CreateRpmCommand(context, upload_manager))
    uploads_section.add_command(package.CreateSrpmCommand(context, upload_manager))
    uploads_section.add_command(errata.CreateErratumCommand(context, upload_manager))
    uploads_section.add_command(package_group.CreatePackageGroupCommand(context, upload_manager))
    uploads_section.add_command(category.CreatePackageCategoryCommand(context, upload_manager))
    uploads_section.add_command(comps.CreateCompsCommand(context, upload_manager))
    uploads_section.add_command(upload.ResumeCommand(context, upload_manager))
    uploads_section.add_command(upload.CancelCommand(context, upload_manager))
    uploads_section.add_command(upload.ListCommand(context, upload_manager))

    sync_section = structure.repo_sync_section(context.cli)
    renderer = status.RpmStatusRenderer(context)
    sync_section.add_command(sync_publish.RunSyncRepositoryCommand(context, renderer))
    sync_section.add_command(sync_publish.SyncStatusCommand(context, renderer))

    publish_section = structure.repo_publish_section(context.cli)
    renderer = PublishStepStatusRenderer(context)
    distributor_id = ids.TYPE_ID_DISTRIBUTOR_YUM
    publish_section.add_command(sync_publish.RunPublishRepositoryCommand(context, renderer,
                                                                         distributor_id))
    publish_section.add_command(sync_publish.PublishStatusCommand(context, renderer))

    repo_export_section = structure.repo_export_section(context.cli)
    renderer = PublishStepStatusRenderer(context)
    repo_export_section.add_command(export.RpmExportCommand(context, renderer))
    repo_export_section.add_command(
        sync_publish.PublishStatusCommand(context, renderer, description=DESC_EXPORT_STATUS))

    sync_schedules_section = structure.repo_sync_schedules_section(context.cli)
    sync_schedules_section.add_command(sync_schedules.RpmCreateScheduleCommand(context))
    sync_schedules_section.add_command(sync_schedules.RpmUpdateScheduleCommand(context))
    sync_schedules_section.add_command(sync_schedules.RpmDeleteScheduleCommand(context))
    sync_schedules_section.add_command(sync_schedules.RpmListScheduleCommand(context))

    sync_schedules_section.add_command(sync_schedules.RpmNextRunCommand(context))


def _upload_manager(context):
    """
    Instantiates and configures the upload manager. The context is used to
    access any necessary configuration.

    :return: initialized and ready to run upload manager instance
    :rtype: UploadManager
    """
    # Each upload_manager needs to be associated with a unique upload working directory.
    # Create a subdirectory for rpm uploads under the main upload_working_dir
    # to avoid interference with other types of uploads eg. iso uploads.
    upload_working_dir = os.path.join(context.config['filesystem']['upload_working_dir'],
                                      RPM_UPLOAD_SUBDIR)
    upload_working_dir = os.path.expanduser(upload_working_dir)
    chunk_size = int(context.config['server']['upload_chunk_size'])
    upload_manager = upload_lib.UploadManager(upload_working_dir, context.server, chunk_size)
    upload_manager.initialize()
    return upload_manager
