"""Doc management commands for ClickUp Framework CLI."""

import sys
import os
from pathlib import Path
from clickup_framework import ClickUpClient, get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def doc_list_command(args):
    """List all docs in a workspace."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get docs
    try:
        result = docs_api.get_workspace_docs(workspace_id)
        docs_list = result.get('docs', [])

        if not docs_list:
            print("No docs found in this workspace")
            return

        # Display header
        use_color = context.get_ansi_output()
        if use_color:
            header = colorize(f"Docs in Workspace {workspace_id}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        else:
            header = f"Docs in Workspace {workspace_id}"
        print(f"\n{header}")
        print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)
        print()

        # Display docs
        for i, doc in enumerate(docs_list, 1):
            doc_name = doc.get('name', 'Unnamed')
            doc_id = doc.get('id', 'Unknown')

            if use_color:
                name_colored = colorize(doc_name, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                id_colored = colorize(f"[{doc_id}]", TextColor.BRIGHT_BLACK)
            else:
                name_colored = doc_name
                id_colored = f"[{doc_id}]"

            print(f"{i}. {name_colored} {id_colored}")

        print()
        print(colorize(f"Total: {len(docs_list)} doc(s)", TextColor.BRIGHT_BLACK) if use_color else f"Total: {len(docs_list)} doc(s)")

    except Exception as e:
        print(f"Error listing docs: {e}", file=sys.stderr)
        sys.exit(1)


def doc_get_command(args):
    """Get and display a specific doc with pages."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)
    use_color = context.get_ansi_output()

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get doc
    try:
        doc = docs_api.get_doc(workspace_id, args.doc_id)

        # Display doc info
        if use_color:
            print(colorize(f"\n📄 Doc: {doc.get('name', 'Unnamed')}", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
            print(colorize(f"ID: {doc.get('id')}", TextColor.BRIGHT_BLACK))
        else:
            print(f"\n📄 Doc: {doc.get('name', 'Unnamed')}")
            print(f"ID: {doc.get('id')}")

        print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)
        print()

        # Get pages
        pages = docs_api.get_doc_pages(workspace_id, args.doc_id)

        if not pages:
            print("No pages in this doc")
            return

        # Display pages
        print(colorize("Pages:", TextColor.BRIGHT_WHITE, TextStyle.BOLD) if use_color else "Pages:")
        print()

        for i, page in enumerate(pages, 1):
            page_name = page.get('name', 'Unnamed')
            page_id = page.get('id', 'Unknown')

            if use_color:
                name_colored = colorize(page_name, TextColor.BRIGHT_WHITE)
                id_colored = colorize(f"[{page_id}]", TextColor.BRIGHT_BLACK)
            else:
                name_colored = page_name
                id_colored = f"[{page_id}]"

            print(f"  {i}. {name_colored} {id_colored}")

            # Show content preview if requested
            if hasattr(args, 'preview') and args.preview:
                content = page.get('content', '')
                if content:
                    # Show first 150 chars
                    preview = content[:150].replace('\n', ' ')
                    if len(content) > 150:
                        preview += "..."
                    print(colorize(f"     {preview}", TextColor.BRIGHT_BLACK) if use_color else f"     {preview}")
                print()

        print()
        print(colorize(f"Total: {len(pages)} page(s)", TextColor.BRIGHT_BLACK) if use_color else f"Total: {len(pages)} page(s)")

    except Exception as e:
        print(f"Error getting doc: {e}", file=sys.stderr)
        sys.exit(1)


def doc_create_command(args):
    """Create a new doc with optional initial pages."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)
    use_color = context.get_ansi_output()

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create doc
    try:
        # Prepare pages if provided
        pages = []
        if hasattr(args, 'pages') and args.pages:
            # Parse pages in format "name:content" or just "name"
            for page_spec in args.pages:
                if ':' in page_spec:
                    name, content = page_spec.split(':', 1)
                    pages.append({'name': name, 'content': content})
                else:
                    pages.append({'name': page_spec, 'content': ''})

        if pages:
            # Create doc with pages
            result = docs_api.create_doc_with_pages(
                workspace_id=workspace_id,
                doc_name=args.name,
                pages=pages
            )
            doc = result['doc']
            created_pages = result['pages']

            # Show success message
            success_msg = ANSIAnimations.success_message(f"Doc created with {len(created_pages)} page(s)")
            print(success_msg)
        else:
            # Create doc without pages
            doc = docs_api.create_doc(workspace_id, args.name)
            success_msg = ANSIAnimations.success_message("Doc created")
            print(success_msg)

        # Display doc info
        print(f"\nDoc Name: {colorize(doc['name'], TextColor.BRIGHT_CYAN) if use_color else doc['name']}")
        print(f"Doc ID: {colorize(doc['id'], TextColor.BRIGHT_GREEN) if use_color else doc['id']}")

        if pages:
            print(f"\nPages created:")
            for i, page in enumerate(created_pages, 1):
                print(f"  {i}. {page['name']} [{page['id']}]")

    except Exception as e:
        print(f"Error creating doc: {e}", file=sys.stderr)
        sys.exit(1)


def doc_update_command(args):
    """Update a page in a doc."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)
    use_color = context.get_ansi_output()

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Update page
    try:
        updated_page = docs_api.update_page(
            workspace_id=workspace_id,
            doc_id=args.doc_id,
            page_id=args.page_id,
            name=args.name if hasattr(args, 'name') and args.name else None,
            content=args.content if hasattr(args, 'content') and args.content else None
        )

        success_msg = ANSIAnimations.success_message("Page updated")
        print(success_msg)
        print(f"\nPage: {colorize(updated_page['name'], TextColor.BRIGHT_CYAN) if use_color else updated_page['name']}")
        print(f"ID: {colorize(updated_page['id'], TextColor.BRIGHT_BLACK) if use_color else updated_page['id']}")

    except Exception as e:
        print(f"Error updating page: {e}", file=sys.stderr)
        sys.exit(1)


def doc_export_command(args):
    """Export docs to markdown files with folder structure."""
    from clickup_framework.resources import DocsAPI

    context = get_context_manager()
    client = ClickUpClient()
    docs_api = DocsAPI(client)
    use_color = context.get_ansi_output()

    # Resolve workspace ID
    try:
        workspace_id = context.resolve_id('workspace', args.workspace_id)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get output directory
    output_dir = Path(args.output_dir if hasattr(args, 'output_dir') and args.output_dir else '.')

    # Export docs
    try:
        if hasattr(args, 'doc_id') and args.doc_id:
            # Export single doc
            doc = docs_api.get_doc(workspace_id, args.doc_id)
            pages = docs_api.get_doc_pages(workspace_id, args.doc_id)

            # Create doc folder
            doc_folder = output_dir / doc['name'].replace('/', '_')
            doc_folder.mkdir(parents=True, exist_ok=True)

            # Export main doc file with metadata
            doc_file = doc_folder / f"{doc['name']}.md"
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(f"# {doc['name']}\n\n")
                f.write(f"**Doc ID:** {doc['id']}\n\n")
                f.write(f"---\n\n")

                # Export pages
                for page in pages:
                    page_name = page.get('name', 'Unnamed')

                    if hasattr(args, 'nested') and args.nested:
                        # Create nested structure based on page names
                        page_path_parts = page_name.split('/')
                        if len(page_path_parts) > 1:
                            page_folder = doc_folder / '/'.join(page_path_parts[:-1])
                            page_folder.mkdir(parents=True, exist_ok=True)
                            page_file = page_folder / f"{page_path_parts[-1]}.md"
                        else:
                            page_file = doc_folder / f"{page_name}.md"
                    else:
                        # Flat structure
                        page_file = doc_folder / f"{page_name.replace('/', '_')}.md"

                    # Write page content
                    with open(page_file, 'w', encoding='utf-8') as pf:
                        pf.write(f"# {page_name}\n\n")
                        pf.write(page.get('content', ''))

                    print(f"Exported: {page_file}")

            success_msg = ANSIAnimations.success_message(f"Exported doc to {doc_folder}")
            print(f"\n{success_msg}")

        else:
            # Export all docs in workspace
            result = docs_api.get_workspace_docs(workspace_id)
            docs_list = result.get('docs', [])

            for doc in docs_list:
                doc_id = doc['id']
                doc_name = doc.get('name', 'Unnamed')

                # Create doc folder
                doc_folder = output_dir / doc_name.replace('/', '_')
                doc_folder.mkdir(parents=True, exist_ok=True)

                # Get pages
                pages = docs_api.get_doc_pages(workspace_id, doc_id)

                # Export each page
                for page in pages:
                    page_name = page.get('name', 'Unnamed')

                    if hasattr(args, 'nested') and args.nested:
                        # Create nested structure
                        page_path_parts = page_name.split('/')
                        if len(page_path_parts) > 1:
                            page_folder = doc_folder / '/'.join(page_path_parts[:-1])
                            page_folder.mkdir(parents=True, exist_ok=True)
                            page_file = page_folder / f"{page_path_parts[-1]}.md"
                        else:
                            page_file = doc_folder / f"{page_name}.md"
                    else:
                        # Flat structure
                        page_file = doc_folder / f"{page_name.replace('/', '_')}.md"

                    # Write page content
                    with open(page_file, 'w', encoding='utf-8') as pf:
                        pf.write(f"# {page_name}\n\n")
                        pf.write(page.get('content', ''))

                    print(f"Exported: {page_file}")

                print(colorize(f"✓ Exported doc: {doc_name}", TextColor.BRIGHT_GREEN) if use_color else f"✓ Exported doc: {doc_name}")

            success_msg = ANSIAnimations.success_message(f"Exported {len(docs_list)} doc(s) to {output_dir}")
            print(f"\n{success_msg}")

    except Exception as e:
        print(f"Error exporting docs: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers):
    """Register doc management commands."""
    # Doc list
    doc_list_parser = subparsers.add_parser('dlist', aliases=['dl', 'doc_list'],
                                            help='List all docs in a workspace')
    doc_list_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_list_parser.set_defaults(func=doc_list_command)

    # Doc get
    doc_get_parser = subparsers.add_parser('doc_get', aliases=['dg'],
                                           help='Get and display a doc with pages')
    doc_get_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_get_parser.add_argument('doc_id', help='Doc ID')
    doc_get_parser.add_argument('--preview', action='store_true',
                                help='Show content preview for each page')
    doc_get_parser.set_defaults(func=doc_get_command)

    # Doc create
    doc_create_parser = subparsers.add_parser('doc_create', aliases=['dc'],
                                              help='Create new doc with optional pages')
    doc_create_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_create_parser.add_argument('name', help='Doc name')
    doc_create_parser.add_argument('--pages', nargs='+',
                                   help='Pages in format "name" or "name:content"')
    doc_create_parser.set_defaults(func=doc_create_command)

    # Doc update
    doc_update_parser = subparsers.add_parser('doc_update', aliases=['du'],
                                              help='Update a page in a doc')
    doc_update_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_update_parser.add_argument('doc_id', help='Doc ID')
    doc_update_parser.add_argument('page_id', help='Page ID')
    doc_update_parser.add_argument('--name', help='New page name')
    doc_update_parser.add_argument('--content', help='New page content (markdown)')
    doc_update_parser.set_defaults(func=doc_update_command)

    # Doc export
    doc_export_parser = subparsers.add_parser('doc_export', aliases=['de'],
                                              help='Export docs to markdown files')
    doc_export_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_export_parser.add_argument('--doc-id', dest='doc_id',
                                   help='Specific doc ID to export (omit to export all)')
    doc_export_parser.add_argument('--output-dir', dest='output_dir', default='.',
                                   help='Output directory (default: current directory)')
    doc_export_parser.add_argument('--nested', action='store_true',
                                   help='Create nested folder structure based on page names')
    doc_export_parser.set_defaults(func=doc_export_command)
