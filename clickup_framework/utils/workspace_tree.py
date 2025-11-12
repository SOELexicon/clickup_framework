"""Workspace tree display utilities for showing accessible lists and folders."""

from typing import Dict, Any, List
from clickup_framework.utils.colors import colorize, TextColor, TextStyle


def display_workspace_tree(workspace_data: Dict[str, Any], show_descriptions: bool = True):
    """
    Display workspace hierarchy in a tree format showing accessible spaces, folders, and lists.

    Args:
        workspace_data: Workspace hierarchy data from get_workspace_hierarchy()
        show_descriptions: Whether to show descriptions for spaces/folders/lists
    """
    workspace_name = workspace_data.get('name', 'Workspace')
    workspace_id = workspace_data.get('id', 'Unknown')

    print(f"\n{colorize('Accessible Workspace Structure:', TextStyle.BOLD)}")
    print(f"📁 {colorize(workspace_name, TextColor.BRIGHT_CYAN, TextStyle.BOLD)} [{colorize(workspace_id, TextColor.BRIGHT_BLACK)}]")

    spaces = workspace_data.get('spaces', [])

    for space_idx, space in enumerate(spaces):
        is_last_space = space_idx == len(spaces) - 1
        space_prefix = "└── " if is_last_space else "├── "
        continuation_prefix = "    " if is_last_space else "│   "

        space_name = space.get('name', 'Unnamed Space')
        space_id = space.get('id', 'Unknown')

        print(f"{space_prefix}📂 {colorize(space_name, TextColor.BRIGHT_GREEN, TextStyle.BOLD)} [{colorize(space_id, TextColor.BRIGHT_BLACK)}]")

        # Show space description if available and requested
        if show_descriptions and space.get('description'):
            desc = space['description'][:80] + "..." if len(space.get('description', '')) > 80 else space.get('description', '')
            print(f"{continuation_prefix}   💬 {colorize(desc, TextColor.BRIGHT_BLACK)}")

        # Process folders
        folders = space.get('folders', [])
        lists = space.get('lists', [])

        # Determine if we have both folders and lists at space level
        has_items = bool(folders or lists)

        for folder_idx, folder in enumerate(folders):
            is_last_folder = folder_idx == len(folders) - 1 and not lists
            folder_prefix = f"{continuation_prefix}└── " if is_last_folder else f"{continuation_prefix}├── "
            folder_continuation = f"{continuation_prefix}    " if is_last_folder else f"{continuation_prefix}│   "

            folder_name = folder.get('name', 'Unnamed Folder')
            folder_id = folder.get('id', 'Unknown')

            print(f"{folder_prefix}📁 {colorize(folder_name, TextColor.BRIGHT_YELLOW)} [{colorize(folder_id, TextColor.BRIGHT_BLACK)}]")

            # Show folder description if available and requested
            if show_descriptions and folder.get('description'):
                desc = folder['description'][:80] + "..." if len(folder.get('description', '')) > 80 else folder.get('description', '')
                print(f"{folder_continuation}   💬 {colorize(desc, TextColor.BRIGHT_BLACK)}")

            # Process lists within folder
            folder_lists = folder.get('lists', [])
            for list_idx, lst in enumerate(folder_lists):
                is_last_list = list_idx == len(folder_lists) - 1
                list_prefix = f"{folder_continuation}└── " if is_last_list else f"{folder_continuation}├── "
                list_continuation = f"{folder_continuation}    " if is_last_list else f"{folder_continuation}│   "

                list_name = lst.get('name', 'Unnamed List')
                list_id = lst.get('id', 'Unknown')

                print(f"{list_prefix}📋 {colorize(list_name, TextColor.BRIGHT_MAGENTA)} [{colorize(list_id, TextColor.BRIGHT_BLACK)}]")

                # Show list description if available and requested
                if show_descriptions and lst.get('description'):
                    desc = lst['description'][:80] + "..." if len(lst.get('description', '')) > 80 else lst.get('description', '')
                    print(f"{list_continuation}   💬 {colorize(desc, TextColor.BRIGHT_BLACK)}")

        # Process lists directly under space (not in folders)
        for list_idx, lst in enumerate(lists):
            is_last_list = list_idx == len(lists) - 1
            list_prefix = f"{continuation_prefix}└── " if is_last_list else f"{continuation_prefix}├── "
            list_continuation = f"{continuation_prefix}    " if is_last_list else f"{continuation_prefix}│   "

            list_name = lst.get('name', 'Unnamed List')
            list_id = lst.get('id', 'Unknown')

            print(f"{list_prefix}📋 {colorize(list_name, TextColor.BRIGHT_MAGENTA)} [{colorize(list_id, TextColor.BRIGHT_BLACK)}]")

            # Show list description if available and requested
            if show_descriptions and lst.get('description'):
                desc = lst['description'][:80] + "..." if len(lst.get('description', '')) > 80 else lst.get('description', '')
                print(f"{list_continuation}   💬 {colorize(desc, TextColor.BRIGHT_BLACK)}")


def display_workspace_tree_on_access_error(client, workspace_id: str):
    """
    Display workspace tree when user encounters an access error.

    Args:
        client: ClickUpClient instance
        workspace_id: Workspace ID to fetch hierarchy for
    """
    try:
        # Get spaces from the workspace
        spaces_response = client.get_team_spaces(workspace_id)
        spaces = spaces_response.get('spaces', [])

        if not spaces:
            print(f"\n{colorize('Unable to fetch accessible lists.', TextColor.BRIGHT_YELLOW, TextStyle.BOLD)}")
            print(f"\nYou can try:")
            print(f"  • {colorize('cum hierarchy --all', TextColor.BRIGHT_BLACK)} - View all accessible tasks")
            print(f"  • {colorize('cum show', TextColor.BRIGHT_BLACK)} - View current context")
            return

        access_msg = "It looks like you don't have access to that list."
        print(f"\n{colorize(access_msg, TextColor.BRIGHT_YELLOW, TextStyle.BOLD)}")
        print(f"{colorize('Here are the lists you can access:', TextColor.BRIGHT_YELLOW)}\n")

        # Fetch folders and lists for each space
        for space in spaces:
            space_id = space.get('id')
            try:
                # Get folders in the space (with their lists)
                folders_response = client._request('GET', f'space/{space_id}/folder')
                space['folders'] = folders_response.get('folders', [])

                # Get folderless lists in the space
                lists_response = client._request('GET', f'space/{space_id}/list')
                space['lists'] = lists_response.get('lists', [])
            except Exception:
                # If we can't fetch a space's details, just skip it
                space['folders'] = []
                space['lists'] = []

        # Build workspace data structure for display
        workspace_data = {
            'name': 'Workspace',
            'id': workspace_id,
            'spaces': spaces
        }

        display_workspace_tree(workspace_data, show_descriptions=False)

        print(f"\n{colorize('💡 Tip:', TextColor.BRIGHT_CYAN, TextStyle.BOLD)} Copy a list ID from above and use it with {colorize('--list <list_id>', TextColor.BRIGHT_BLACK)}")
        print(f"   Or set it as current: {colorize('cum set list <list_id>', TextColor.BRIGHT_BLACK)}")

    except Exception as e:
        # If we can't fetch hierarchy, just show the basic error
        print(f"\n{colorize('Unable to fetch workspace hierarchy:', TextColor.BRIGHT_RED)} {e}")
        print(f"\nYou can try:")
        print(f"  • {colorize('cum hierarchy --all', TextColor.BRIGHT_BLACK)} - View all accessible tasks")
        print(f"  • {colorize('cum show', TextColor.BRIGHT_BLACK)} - View current context")


def collect_all_list_ids(workspace_data: Dict[str, Any]) -> List[str]:
    """
    Collect all list IDs from workspace hierarchy.

    Args:
        workspace_data: Workspace hierarchy data from get_workspace_hierarchy()

    Returns:
        List of all accessible list IDs
    """
    list_ids = []

    spaces = workspace_data.get('spaces', [])
    for space in spaces:
        # Lists directly under space
        for lst in space.get('lists', []):
            list_ids.append(lst.get('id'))

        # Lists in folders
        for folder in space.get('folders', []):
            for lst in folder.get('lists', []):
                list_ids.append(lst.get('id'))

    return list_ids
