"""
Hierarchy view command - displays tasks in parent-child hierarchy.

This module provides the `hierarchy` command (and its aliases: h, list, ls, l) which
displays ClickUp tasks in a hierarchical tree structure showing parent-child relationships.
"""

import sys
import logging
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.components import DisplayManager
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.commands.utils import create_format_options, get_list_statuses, add_common_args, resolve_container_id

logger = logging.getLogger(__name__)


def _hierarchy_impl(args, context, client, use_color):
    """
    Display tasks in hierarchical parent-child view with full pagination support.
    """
    display = DisplayManager(client)

    # Check if --all flag is set
    show_all = getattr(args, 'show_all', False)

    # Check if --space flag is set
    space_id = getattr(args, 'space_id', None)

    # If --space is provided, use it as the list_id
    if space_id:
        args.list_id = space_id

    # Get the include_completed and show_closed_only flags
    include_completed = getattr(args, 'include_completed', False)
    show_closed_only = getattr(args, 'show_closed_only', False)
    include_closed = include_completed or show_closed_only

    # Validate that either list_id or --all is provided
    if not show_all and not args.list_id:
        print("Error: Either provide a container ID, use --space, or use --all to show all workspace tasks", file=sys.stderr)
        sys.exit(1)

    if show_all and args.list_id:
        print("Error: Cannot use both container ID/--space and --all flag together", file=sys.stderr)
        sys.exit(1)

    if show_all:
        try:
            team_id = context.resolve_id('workspace', 'current')
        except ValueError:
            print("Error: No workspace ID set. Use 'cum set workspace <team_id>' first.", file=sys.stderr)
            sys.exit(1)

        tasks = _fetch_all_pages(
            lambda **p: client.get_team_tasks(team_id, **p),
            subtasks=True,
            include_closed=include_closed
        )
        list_id = None
        container_name = None
    else:
        try:
            container = resolve_container_id(client, args.list_id, context)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        container_type = container['type']
        container_id = container['id']

        if container_type == 'space':
            space_data = container['data']
            container_name = space_data.get('name', 'Space')
            tasks = _get_tasks_from_space(client, space_data, include_closed)
            colorize_val = getattr(args, 'colorize', None)
            use_color_val = colorize_val if colorize_val is not None else context.get_ansi_output()
            tasks = _wrap_space_tasks_in_containers(tasks, space_data, use_color_val)
            list_id = None
        elif container_type == 'folder':
            folder_data = container['data']
            container_name = folder_data.get('name', 'Folder')
            tasks = _get_tasks_from_folder(client, folder_data, include_closed)
            colorize_val = getattr(args, 'colorize', None)
            use_color_val = colorize_val if colorize_val is not None else context.get_ansi_output()
            tasks = _wrap_folder_tasks_in_lists(tasks, folder_data, use_color_val)
            list_id = None
        elif container_type == 'task':
            task_data = container['data']
            list_id_for_fetch = container['list_id']
            container_name = task_data.get('name', 'Task')

            root_tasks = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id_for_fetch, **p),
                include_closed=include_closed
            )
            subtask_list = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id_for_fetch, **p),
                subtasks='true',
                include_closed=include_closed
            )

            task_map = {}
            for task in root_tasks + subtask_list:
                task_map[task['id']] = task
            all_tasks = list(task_map.values())
            tasks = _filter_task_and_descendants(all_tasks, container_id)
            list_id = None
        else:  # container_type == 'list'
            list_id = container_id
            root_tasks = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id, **p),
                include_closed=include_closed
            )
            subtask_list = _fetch_all_pages(
                lambda **p: client.get_list_tasks(list_id, **p),
                subtasks='true',
                include_closed=include_closed
            )

            task_map = {}
            for task in root_tasks + subtask_list:
                task_map[task['id']] = task
            tasks = list(task_map.values())
            container_name = None

    options = create_format_options(args)
    if not show_all and args.list_id and container_type == 'task':
        options.highlight_task_id = container_id

    if list_id:
        colorize_val = getattr(args, 'colorize', None)
        use_color_val = colorize_val if colorize_val is not None else context.get_ansi_output()
        status_line = get_list_statuses(client, list_id, use_color=use_color_val)
        if status_line:
            print(status_line)
            print()

    header = getattr(args, "header", None)
    if not header:
        if show_all: header = "All Workspace Tasks"
        elif container_name: header = f"Tasks in {container_name}"
        else: header = "Tasks"

    if not show_all and args.list_id and tasks and container_type == 'task':
        options.show_containers = True
        options.container_info = {
            'space': tasks[0].get('space') if tasks else None,
            'folder': tasks[0].get('folder') if tasks else None,
            'list': tasks[0].get('list') if tasks else None,
            'use_color': context.get_ansi_output()
        }

    output = display.hierarchy_view(tasks, options, header=header)
    return tasks, output


def _wrap_tasks_in_containers(tasks, use_color=True):
    if not tasks: return None
    from clickup_framework.utils.colors import colorize, TextColor, TextStyle
    first_task = tasks[0]
    current_children = tasks

    if first_task.get('list'):
        list_obj = first_task['list']
        list_name = list_obj.get('name', 'Unknown List') if isinstance(list_obj, dict) else str(list_obj)
        list_id = list_obj.get('id', '') if isinstance(list_obj, dict) else ''
        if use_color:
            list_display = colorize(list_name, TextColor.CYAN, TextStyle.BOLD)
            if list_id: list_display += colorize(f" [{list_id}]", TextColor.BRIGHT_BLACK)
            list_display += colorize(" (list)", TextColor.BRIGHT_BLACK)
        else:
            list_display = f"{list_name} [{list_id}] (list)" if list_id else f"{list_name} (list)"
        list_node = {'id': 'container_list', 'name': list_display, 'custom_type': 'container', '_children': current_children, '_is_container': True}
        current_children = [list_node]

    if first_task.get('folder'):
        folder = first_task['folder']
        folder_name = folder.get('name', 'Unknown Folder') if isinstance(folder, dict) else str(folder)
        folder_id = folder.get('id', '') if isinstance(folder, dict) else ''
        if use_color:
            folder_display = colorize(folder_name, TextColor.YELLOW, TextStyle.BOLD)
            if folder_id: folder_display += colorize(f" [{folder_id}]", TextColor.BRIGHT_BLACK)
            folder_display += colorize(" (folder)", TextColor.BRIGHT_BLACK)
        else:
            folder_display = f"{folder_name} [{folder_id}] (folder)" if folder_id else f"{folder_name} (folder)"
        folder_node = {'id': 'container_folder', 'name': folder_display, 'custom_type': 'container', '_children': current_children, '_is_container': True}
        current_children = [folder_node]

    if first_task.get('space'):
        space = first_task['space']
        space_name = space.get('name', '') if isinstance(space, dict) else str(space)
        if space_name:
            if use_color:
                space_display = colorize(space_name, TextColor.BRIGHT_MAGENTA, TextStyle.BOLD) + colorize(" (workspace)", TextColor.BRIGHT_BLACK)
            else:
                space_display = f"{space_name} (workspace)"
            space_node = {'id': 'container_workspace', 'name': space_display, 'custom_type': 'container', '_children': current_children, '_is_container': True}
            current_children = [space_node]
    return current_children


def _wrap_space_tasks_in_containers(tasks, space_data, use_color=True):
    if not tasks: return []
    from clickup_framework.utils.colors import colorize, TextColor, TextStyle
    from collections import defaultdict
    tasks_by_folder_and_list = defaultdict(lambda: defaultdict(list))
    folderless_tasks_by_list = defaultdict(list)

    for task in tasks:
        f_info = task.get('folder', {})
        l_info = task.get('list', {})
        f_id = f_info.get('id') if isinstance(f_info, dict) else (str(f_info) if f_info else None)
        l_id = l_info.get('id') if isinstance(l_info, dict) else (str(l_info) if l_info else None)
        if f_id and l_id: tasks_by_folder_and_list[f_id][l_id].append(task)
        elif l_id: folderless_tasks_by_list[l_id].append(task)

    folders_metadata = {fld.get('id'): fld for fld in space_data.get('folders', [])}
    all_lists_metadata = {}
    for fld in space_data.get('folders', []):
        for lst in fld.get('lists', []): all_lists_metadata[lst.get('id')] = lst
    for lst in space_data.get('lists', []): all_lists_metadata[lst.get('id')] = lst

    nodes = []
    for f_id, lists_in_f in tasks_by_folder_and_list.items():
        f_meta = folders_metadata.get(f_id, {})
        f_name = f_meta.get('name', 'Unknown Folder')
        f_disp = colorize(f_name, TextColor.YELLOW, TextStyle.BOLD) + colorize(f" [{f_id}] (folder)", TextColor.BRIGHT_BLACK) if use_color else f"{f_name} [{f_id}] (folder)"
        l_nodes = []
        for l_id, l_tasks in lists_in_f.items():
            l_meta = all_lists_metadata.get(l_id, {})
            l_name = l_meta.get('name', 'Unknown List')
            l_disp = colorize(l_name, TextColor.CYAN, TextStyle.BOLD) + colorize(f" [{l_id}] (list)", TextColor.BRIGHT_BLACK) if use_color else f"{l_name} [{l_id}] (list)"
            l_nodes.append({'id': f'container_list_{l_id}', 'name': l_disp, 'custom_type': 'container', '_children': l_tasks, '_is_container': True})
        l_nodes.sort(key=lambda x: x['name'])
        nodes.append({'id': f'container_folder_{f_id}', 'name': f_disp, 'custom_type': 'container', '_children': l_nodes, '_is_container': True})

    for l_id, l_tasks in folderless_tasks_by_list.items():
        l_meta = all_lists_metadata.get(l_id, {})
        l_name = l_meta.get('name', 'Unknown List')
        l_disp = colorize(l_name, TextColor.CYAN, TextStyle.BOLD) + colorize(f" [{l_id}] (list)", TextColor.BRIGHT_BLACK) if use_color else f"{l_name} [{l_id}] (list)"
        nodes.append({'id': f'container_list_{l_id}', 'name': l_disp, 'custom_type': 'container', '_children': l_tasks, '_is_container': True})
    nodes.sort(key=lambda x: x['name'])
    return nodes


def _wrap_folder_tasks_in_lists(tasks, folder_data, use_color=True):
    if not tasks: return []
    from clickup_framework.utils.colors import colorize, TextColor, TextStyle
    from collections import defaultdict
    tasks_by_list = defaultdict(list)
    for task in tasks:
        l_info = task.get('list', {})
        l_id = l_info.get('id') if isinstance(l_info, dict) else (str(l_info) if l_info else None)
        if l_id: tasks_by_list[l_id].append(task)

    l_containers = []
    l_metadata = {lst.get('id'): lst for lst in folder_data.get('lists', [])}
    for l_id, l_tasks in tasks_by_list.items():
        l_meta = l_metadata.get(l_id, {})
        l_name = l_meta.get('name', 'Unknown List')
        l_disp = colorize(l_name, TextColor.CYAN, TextStyle.BOLD) + colorize(f" [{l_id}] (list)", TextColor.BRIGHT_BLACK) if use_color else f"{l_name} [{l_id}] (list)"
        l_containers.append({'id': f'container_list_{l_id}', 'name': l_disp, 'custom_type': 'container', '_children': l_tasks, '_is_container': True})
    l_containers.sort(key=lambda x: x['name'])
    return l_containers


def _fetch_all_pages(fetch_func, **params):
    all_tasks, page, last_page = [], 0, False
    while not last_page:
        try:
            result = fetch_func(page=page, **params)
            all_tasks.extend(result.get('tasks', []))
            last_page = result.get('last_page', True)
            page += 1
        except Exception as e:
            logger.warning(f"Pagination stopped at page {page}: {e}")
            break
    return all_tasks


def _get_tasks_from_lists(client, lists, include_closed=False):
    from clickup_framework.exceptions import ClickUpNotFoundError, ClickUpAuthError
    tasks = []
    for item in lists:
        l_id = item.get('id')
        if l_id:
            try:
                tasks.extend(_fetch_all_pages(lambda **p: client.get_list_tasks(l_id, **p), include_closed=include_closed))
            except (ClickUpNotFoundError, ClickUpAuthError) as e: logger.debug(f"Failed list {l_id}: {e}")
            except Exception as e: logger.warning(f"Error list {l_id}: {e}")
    return tasks


def _get_tasks_from_space(client, space_data, include_closed=False):
    tasks = []
    for folder in space_data.get('folders', []):
        tasks.extend(_get_tasks_from_lists(client, folder.get('lists', []), include_closed))
    tasks.extend(_get_tasks_from_lists(client, space_data.get('lists', []), include_closed))
    return tasks


def _get_tasks_from_folder(client, folder_data, include_closed=False):
    return _get_tasks_from_lists(client, folder_data.get('lists', []), include_closed)


def _filter_task_and_descendants(all_tasks, root_task_id):
    task_map = {task['id']: task for task in all_tasks}
    if root_task_id not in task_map: return []
    def collect(tid, coll):
        if tid in task_map:
            coll.append(task_map[tid])
            for child in all_tasks:
                if child.get('parent') == tid: collect(child['id'], coll)
    res = []
    collect(root_task_id, res)
    return res


class HierarchyCommand(BaseCommand):
    def _get_context_manager(self): return get_context_manager()
    def _create_client(self): return ClickUpClient()
    def execute(self):
        tasks, output = _hierarchy_impl(self.args, self.context, self.client, self.use_color)
        from clickup_framework.components.display import DisplayManager
        display_mgr = DisplayManager(self.client)
        self.handle_output(data=tasks, formatter=display_mgr.hierarchy_formatter, detail_level=getattr(self.args, 'preset', 'full'), console_output=output)
        if getattr(self.args, 'output', 'console') == 'console':
            from clickup_framework.components.tips import show_tip
            show_tip('hierarchy', use_color=self.use_color, enabled=getattr(self.args, 'show_tips', True))
        return tasks, output


def hierarchy_command(args):
    command = HierarchyCommand(args, command_name='hierarchy')
    command.execute()


def register_command(subparsers):
    parsers = []
    for name, help_text in [
        ('hierarchy', 'Display tasks in hierarchical view'),
        ('h', 'Display tasks in hierarchical view (alias)'),
        ('list', 'Display tasks in hierarchical view (alias)'),
        ('ls', 'Display tasks in hierarchical view (alias)'),
        ('l', 'Display tasks in hierarchical view (alias)')
    ]:
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument('list_id', nargs='?', help='ClickUp space, folder, list, or task ID')
        p.add_argument('--header', help='Custom header text')
        p.add_argument('--all', dest='show_all', action='store_true', help='Show all tasks from entire workspace')
        p.add_argument('--space', dest='space_id', help='Show all in specific space')
        p.add_argument('--depth', type=int, help='Limit depth')
        add_common_args(p)
        p.set_defaults(func=hierarchy_command, preset='full')
        parsers.append(p)
