"""Doc management commands for ClickUp Framework CLI."""

import os
from pathlib import Path
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations
from clickup_framework.utils.text import unescape_content


class DocListCommand(BaseCommand):
    """List all docs in a workspace."""

    def execute(self):
        """Execute the doc list command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)

        # Get docs
        try:
            result = docs_api.get_workspace_docs(workspace_id)
            docs_list = result.get('docs', [])

            if not docs_list:
                self.print("No docs found in this workspace")
                return

            # Display header
            use_color = self.context.get_ansi_output()
            if use_color:
                header = colorize(f"Docs in Workspace {workspace_id}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            else:
                header = f"Docs in Workspace {workspace_id}"
            self.print(f"\n{header}")
            self.print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)
            self.print()

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

                self.print(f"{i}. {name_colored} {id_colored}")

            self.print()
            self.print(colorize(f"Total: {len(docs_list)} doc(s)", TextColor.BRIGHT_BLACK) if use_color else f"Total: {len(docs_list)} doc(s)")

        except Exception as e:
            self.error(f"Error listing docs: {e}")


class DocGetCommand(BaseCommand):
    """Get and display a specific doc with pages."""

    def execute(self):
        """Execute the doc get command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)

        # Get doc
        try:
            doc = docs_api.get_doc(workspace_id, self.args.doc_id)

            # Display doc info
            if use_color:
                self.print(colorize(f"\n📄 Doc: {doc.get('name', 'Unnamed')}", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
                self.print(colorize(f"ID: {doc.get('id')}", TextColor.BRIGHT_BLACK))
            else:
                self.print(f"\n📄 Doc: {doc.get('name', 'Unnamed')}")
                self.print(f"ID: {doc.get('id')}")

            self.print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)
            self.print()

            # Get pages
            pages = docs_api.get_doc_pages(workspace_id, self.args.doc_id)

            if not pages:
                self.print("No pages in this doc")
                return

            # Display pages
            self.print(colorize("Pages:", TextColor.BRIGHT_WHITE, TextStyle.BOLD) if use_color else "Pages:")
            self.print()

            for i, page in enumerate(pages, 1):
                page_name = page.get('name', 'Unnamed')
                page_id = page.get('id', 'Unknown')

                if use_color:
                    name_colored = colorize(page_name, TextColor.BRIGHT_WHITE)
                    id_colored = colorize(f"[{page_id}]", TextColor.BRIGHT_BLACK)
                else:
                    name_colored = page_name
                    id_colored = f"[{page_id}]"

                self.print(f"  {i}. {name_colored} {id_colored}")

                # Show content preview if requested
                if hasattr(self.args, 'preview') and self.args.preview:
                    content = page.get('content', '')
                    if content:
                        # Unescape content from ClickUp API
                        content = unescape_content(content)
                        # Show first 150 chars
                        preview = content[:150].replace('\n', ' ')
                        if len(content) > 150:
                            preview += "..."
                        self.print(colorize(f"     {preview}", TextColor.BRIGHT_BLACK) if use_color else f"     {preview}")
                    self.print()

            self.print()
            self.print(colorize(f"Total: {len(pages)} page(s)", TextColor.BRIGHT_BLACK) if use_color else f"Total: {len(pages)} page(s)")

        except Exception as e:
            self.error(f"Error getting doc: {e}")


class DocCreateCommand(BaseCommand):
    """Create a new doc with optional initial pages."""

    def execute(self):
        """Execute the doc create command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)

        # Create doc
        try:
            # Prepare pages if provided
            pages = []
            if hasattr(self.args, 'pages') and self.args.pages:
                # Parse pages in format "name:content" or just "name"
                for page_spec in self.args.pages:
                    if ':' in page_spec:
                        name, content = page_spec.split(':', 1)
                        pages.append({'name': name, 'content': content})
                    else:
                        pages.append({'name': page_spec, 'content': ''})

            if pages:
                # Create doc with pages
                result = docs_api.create_doc_with_pages(
                    workspace_id=workspace_id,
                    doc_name=self.args.name,
                    pages=pages
                )
                doc = result['doc']
                created_pages = result['pages']

                # Show success message
                success_msg = ANSIAnimations.success_message(f"Doc created with {len(created_pages)} page(s)")
                self.print(success_msg)
            else:
                # Create doc without pages
                doc = docs_api.create_doc(workspace_id, self.args.name)
                success_msg = ANSIAnimations.success_message("Doc created")
                self.print(success_msg)

            # Display doc info
            self.print(f"\nDoc Name: {colorize(doc['name'], TextColor.BRIGHT_CYAN) if use_color else doc['name']}")
            self.print(f"Doc ID: {colorize(doc['id'], TextColor.BRIGHT_GREEN) if use_color else doc['id']}")

            if pages:
                self.print(f"\nPages created:")
                for i, page in enumerate(created_pages, 1):
                    self.print(f"  {i}. {page['name']} [{page['id']}]")

        except Exception as e:
            self.error(f"Error creating doc: {e}")


class DocUpdateCommand(BaseCommand):
    """Update a page in a doc."""

    def execute(self):
        """Execute the doc update command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)

        # Update page
        try:
            updated_page = docs_api.update_page(
                workspace_id=workspace_id,
                doc_id=self.args.doc_id,
                page_id=self.args.page_id,
                name=self.args.name if hasattr(self.args, 'name') and self.args.name else None,
                content=self.args.content if hasattr(self.args, 'content') and self.args.content else None
            )

            success_msg = ANSIAnimations.success_message("Page updated")
            self.print(success_msg)
            self.print(f"\nPage: {colorize(updated_page['name'], TextColor.BRIGHT_CYAN) if use_color else updated_page['name']}")
            self.print(f"ID: {colorize(updated_page['id'], TextColor.BRIGHT_BLACK) if use_color else updated_page['id']}")

        except Exception as e:
            self.error(f"Error updating page: {e}")


class DocExportCommand(BaseCommand):
    """Export docs to markdown files with folder structure."""

    def execute(self):
        """Execute the doc export command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)

        # Get output directory
        output_dir = Path(self.args.output_dir if hasattr(self.args, 'output_dir') and self.args.output_dir else '.')

        # Export docs
        try:
            if hasattr(self.args, 'doc_id') and self.args.doc_id:
                # Export single doc
                doc = docs_api.get_doc(workspace_id, self.args.doc_id)
                pages = docs_api.get_doc_pages(workspace_id, self.args.doc_id)

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

                        if hasattr(self.args, 'nested') and self.args.nested:
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
                            # Unescape content from ClickUp API before writing
                            content = unescape_content(page.get('content', ''))
                            pf.write(content)

                        self.print(f"Exported: {page_file}")

                success_msg = ANSIAnimations.success_message(f"Exported doc to {doc_folder}")
                self.print(f"\n{success_msg}")

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

                        if hasattr(self.args, 'nested') and self.args.nested:
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
                            # Unescape content from ClickUp API before writing
                            content = unescape_content(page.get('content', ''))
                            pf.write(content)

                        self.print(f"Exported: {page_file}")

                    self.print(colorize(f"✓ Exported doc: {doc_name}", TextColor.BRIGHT_GREEN) if use_color else f"✓ Exported doc: {doc_name}")

                success_msg = ANSIAnimations.success_message(f"Exported {len(docs_list)} doc(s) to {output_dir}")
                self.print(f"\n{success_msg}")

        except Exception as e:
            self.error(f"Error exporting docs: {e}")


class DocImportCommand(BaseCommand):
    """Import markdown files from a directory structure to create docs and pages."""

    def execute(self):
        """Execute the doc import command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)

        # Get input directory
        input_dir = Path(self.args.input_dir)
        if not input_dir.exists():
            self.error(f"Error: Directory {input_dir} does not exist")

        # Import docs
        try:
            if hasattr(self.args, 'doc_name') and self.args.doc_name:
                # Import single doc from directory
                doc_folder = input_dir
                if not doc_folder.is_dir():
                    self.error(f"Error: {doc_folder} is not a directory")

                # Find all markdown files
                md_files = list(doc_folder.glob('*.md'))
                if hasattr(self.args, 'recursive') and self.args.recursive:
                    md_files = list(doc_folder.glob('**/*.md'))

                if not md_files:
                    self.print(f"No markdown files found in {doc_folder}")
                    return

                # Create doc
                doc_name = self.args.doc_name
                self.print(f"Creating doc: {doc_name}...")
                doc = docs_api.create_doc(workspace_id, doc_name)
                doc_id = doc['id']

                # Import pages
                pages_created = 0
                for md_file in md_files:
                    # Read markdown file
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Extract page name from filename or first heading
                    page_name = md_file.stem

                    # If content starts with a heading, use that as the name
                    lines = content.split('\n')
                    if lines and lines[0].startswith('# '):
                        page_name = lines[0][2:].strip()
                        # Remove the heading from content if it matches the filename
                        if page_name == md_file.stem:
                            content = '\n'.join(lines[1:]).lstrip()

                    # Get relative path for nested structure
                    if hasattr(self.args, 'nested') and self.args.nested:
                        rel_path = md_file.relative_to(doc_folder)
                        page_name = str(rel_path.with_suffix('')).replace(os.sep, '/')

                    # Create page
                    page = docs_api.create_page(
                        workspace_id=workspace_id,
                        doc_id=doc_id,
                        name=page_name,
                        content=content
                    )
                    pages_created += 1
                    self.print(f"  Created page: {page_name} [{page['id']}]")

                success_msg = ANSIAnimations.success_message(f"Imported doc with {pages_created} page(s)")
                self.print(f"\n{success_msg}")
                self.print(f"Doc ID: {colorize(doc_id, TextColor.BRIGHT_GREEN) if use_color else doc_id}")

            else:
                # Import multiple docs from directory structure
                # Each subdirectory becomes a doc
                doc_folders = [d for d in input_dir.iterdir() if d.is_dir()]

                if not doc_folders:
                    self.print(f"No subdirectories found in {input_dir}")
                    return

                total_docs = 0
                total_pages = 0

                for doc_folder in doc_folders:
                    # Find markdown files in this folder
                    md_files = list(doc_folder.glob('*.md'))
                    if hasattr(self.args, 'recursive') and self.args.recursive:
                        md_files = list(doc_folder.glob('**/*.md'))

                    if not md_files:
                        continue

                    # Create doc
                    doc_name = doc_folder.name
                    self.print(f"\nCreating doc: {doc_name}...")
                    doc = docs_api.create_doc(workspace_id, doc_name)
                    doc_id = doc['id']
                    total_docs += 1

                    # Import pages
                    pages_created = 0
                    for md_file in md_files:
                        # Read markdown file
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Extract page name from filename or first heading
                        page_name = md_file.stem

                        # If content starts with a heading, use that as the name
                        lines = content.split('\n')
                        if lines and lines[0].startswith('# '):
                            page_name = lines[0][2:].strip()
                            # Remove the heading from content
                            content = '\n'.join(lines[1:]).lstrip()

                        # Get relative path for nested structure
                        if hasattr(self.args, 'nested') and self.args.nested:
                            rel_path = md_file.relative_to(doc_folder)
                            page_name = str(rel_path.with_suffix('')).replace(os.sep, '/')

                        # Create page
                        page = docs_api.create_page(
                            workspace_id=workspace_id,
                            doc_id=doc_id,
                            name=page_name,
                            content=content
                        )
                        pages_created += 1
                        total_pages += 1
                        self.print(f"  Created page: {page_name}")

                    self.print(colorize(f"  ✓ Created {pages_created} page(s) in doc", TextColor.BRIGHT_GREEN) if use_color else f"  ✓ Created {pages_created} page(s) in doc")

                success_msg = ANSIAnimations.success_message(f"Imported {total_docs} doc(s) with {total_pages} total page(s)")
                self.print(f"\n{success_msg}")

        except Exception as e:
            if os.getenv('DEBUG'):
                raise
            self.error(f"Error importing docs: {e}")


class PageListCommand(BaseCommand):
    """List all pages in a doc."""

    def execute(self):
        """Execute the page list command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace and doc IDs
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)
        doc_id = self.args.doc_id

        # Get pages
        try:
            pages = docs_api.get_doc_pages(workspace_id, doc_id)

            if not pages:
                self.print("No pages found in this doc")
                return

            # Get doc info first for display
            doc = docs_api.get_doc(workspace_id, doc_id)

            # Display header
            if use_color:
                header = colorize(f"Pages in Doc: {doc.get('name', 'Unknown')}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
            else:
                header = f"Pages in Doc: {doc.get('name', 'Unknown')}"
            self.print(f"\n{header}")
            self.print(colorize("─" * 60, TextColor.BRIGHT_BLACK) if use_color else "─" * 60)
            self.print()

            # Display pages
            for i, page in enumerate(pages, 1):
                page_name = page.get('name', 'Unnamed')
                page_id = page.get('id', 'Unknown')

                if use_color:
                    name_colored = colorize(page_name, TextColor.BRIGHT_WHITE, TextStyle.BOLD)
                    id_colored = colorize(f"[{page_id}]", TextColor.BRIGHT_BLACK)
                else:
                    name_colored = page_name
                    id_colored = f"[{page_id}]"

                self.print(f"{i}. {name_colored} {id_colored}")

            self.print()
            self.print(colorize(f"Total: {len(pages)} page(s)", TextColor.BRIGHT_BLACK) if use_color else f"Total: {len(pages)} page(s)")

        except Exception as e:
            self.error(f"Error listing pages: {e}")


class PageCreateCommand(BaseCommand):
    """Create a new page in a doc."""

    def execute(self):
        """Execute the page create command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace and doc IDs
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)
        doc_id = self.args.doc_id

        # Create page
        try:
            content = self.args.content if hasattr(self.args, 'content') and self.args.content else ""
            page = docs_api.create_page(
                workspace_id=workspace_id,
                doc_id=doc_id,
                name=self.args.name,
                content=content
            )

            success_msg = ANSIAnimations.success_message("Page created")
            self.print(success_msg)
            self.print(f"\nPage Name: {colorize(page['name'], TextColor.BRIGHT_CYAN) if use_color else page['name']}")
            self.print(f"Page ID: {colorize(page['id'], TextColor.BRIGHT_GREEN) if use_color else page['id']}")

        except Exception as e:
            self.error(f"Error creating page: {e}")


class PageUpdateCommand(BaseCommand):
    """Update a page in a doc."""

    def execute(self):
        """Execute the page update command."""
        from clickup_framework.resources import DocsAPI

        docs_api = DocsAPI(self.client)
        use_color = self.context.get_ansi_output()

        # Resolve workspace ID
        workspace_id = self.resolve_id('workspace', self.args.workspace_id)
        doc_id = self.args.doc_id
        page_id = self.args.page_id

        # Update page
        try:
            updated_page = docs_api.update_page(
                workspace_id=workspace_id,
                doc_id=doc_id,
                page_id=page_id,
                name=self.args.name if hasattr(self.args, 'name') and self.args.name else None,
                content=self.args.content if hasattr(self.args, 'content') and self.args.content else None
            )

            success_msg = ANSIAnimations.success_message("Page updated")
            self.print(success_msg)
            self.print(f"\nPage: {colorize(updated_page['name'], TextColor.BRIGHT_CYAN) if use_color else updated_page['name']}")
            self.print(f"ID: {colorize(updated_page['id'], TextColor.BRIGHT_BLACK) if use_color else updated_page['id']}")

        except Exception as e:
            self.error(f"Error updating page: {e}")


# Backward compatibility wrappers
def doc_list_command(args):
    """Command wrapper for doc list."""
    command = DocListCommand(args, command_name='dlist')
    command.execute()


def doc_get_command(args):
    """Command wrapper for doc get."""
    command = DocGetCommand(args, command_name='doc_get')
    command.execute()


def doc_create_command(args):
    """Command wrapper for doc create."""
    command = DocCreateCommand(args, command_name='doc_create')
    command.execute()


def doc_update_command(args):
    """Command wrapper for doc update."""
    command = DocUpdateCommand(args, command_name='doc_update')
    command.execute()


def doc_export_command(args):
    """Command wrapper for doc export."""
    command = DocExportCommand(args, command_name='doc_export')
    command.execute()


def doc_import_command(args):
    """Command wrapper for doc import."""
    command = DocImportCommand(args, command_name='doc_import')
    command.execute()


def page_list_command(args):
    """Command wrapper for page list."""
    command = PageListCommand(args, command_name='page_list')
    command.execute()


def page_create_command(args):
    """Command wrapper for page create."""
    command = PageCreateCommand(args, command_name='page_create')
    command.execute()


def page_update_command(args):
    """Command wrapper for page update."""
    command = PageUpdateCommand(args, command_name='page_update')
    command.execute()


def register_command(subparsers):
    """Register doc management commands."""
    # Doc list
    doc_list_parser = subparsers.add_parser(
        'dlist',
        aliases=['dl', 'doc_list'],
        help='List all docs in a workspace',
        description='Display all ClickUp Docs in a workspace with their details.',
        epilog='''Tips:
  • List docs in current workspace: cum dlist current
  • List docs in specific workspace: cum dlist 90123456
  • Docs are ClickUp's knowledge base feature
  • Use doc_get to view pages in a specific doc
  • Docs contain one or more pages of content'''
    )
    doc_list_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_list_parser.set_defaults(func=doc_list_command)

    # Doc get
    doc_get_parser = subparsers.add_parser(
        'doc_get',
        aliases=['dg'],
        help='Get and display a doc with pages',
        description='Display a specific ClickUp Doc with all its pages and optional content preview.',
        epilog='''Tips:
  • Get doc details: cum dg current <doc_id>
  • Show page previews: cum dg current <doc_id> --preview
  • Find doc IDs with cum dlist <workspace_id>
  • Use page_list for just page names
  • Use doc_export to save as markdown files'''
    )
    doc_get_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_get_parser.add_argument('doc_id', help='Doc ID')
    doc_get_parser.add_argument('--preview', action='store_true',
                                help='Show content preview for each page')
    doc_get_parser.set_defaults(func=doc_get_command)

    # Doc create
    doc_create_parser = subparsers.add_parser(
        'doc_create',
        aliases=['dc'],
        help='Create new doc with optional pages',
        description='Create a new ClickUp Doc with an optional initial set of pages.',
        epilog='''Tips:
  • Create empty doc: cum dc current "My Doc"
  • Create with pages: cum dc current "My Doc" --pages "Intro" "Setup:Install steps"
  • Page format: "name" or "name:content"
  • Use page_create to add pages later
  • Content can be markdown formatted'''
    )
    doc_create_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_create_parser.add_argument('name', help='Doc name')
    doc_create_parser.add_argument('--pages', nargs='+',
                                   help='Pages in format "name" or "name:content"')
    doc_create_parser.set_defaults(func=doc_create_command)

    # Doc update
    doc_update_parser = subparsers.add_parser(
        'doc_update',
        aliases=['du'],
        help='Update a page in a doc',
        description='Update the name or content of an existing page in a ClickUp Doc.',
        epilog='''Tips:
  • Update page name: cum du current <doc_id> <page_id> --name "New Name"
  • Update content: cum du current <doc_id> <page_id> --content "New content"
  • Update both: cum du current <doc_id> <page_id> --name "New" --content "Updated"
  • Find page IDs with page_list or doc_get
  • Content supports markdown formatting'''
    )
    doc_update_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_update_parser.add_argument('doc_id', help='Doc ID')
    doc_update_parser.add_argument('page_id', help='Page ID')
    doc_update_parser.add_argument('--name', help='New page name')
    doc_update_parser.add_argument('--content', help='New page content (markdown)')
    doc_update_parser.set_defaults(func=doc_update_command)

    # Doc export
    doc_export_parser = subparsers.add_parser(
        'doc_export',
        aliases=['de'],
        help='Export docs to markdown files',
        description='Export ClickUp Docs to local markdown files, preserving structure and content.',
        epilog='''Tips:
  • Export all docs: cum de current --output-dir ./docs
  • Export specific doc: cum de current --doc-id <id> --output-dir ./docs
  • Nested structure: cum de current --nested (preserves page hierarchy)
  • Creates folder per doc with .md files for pages
  • Great for version control and offline access'''
    )
    doc_export_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_export_parser.add_argument('--doc-id', dest='doc_id',
                                   help='Specific doc ID to export (omit to export all)')
    doc_export_parser.add_argument('--output-dir', dest='output_dir', default='.',
                                   help='Output directory (default: current directory)')
    doc_export_parser.add_argument('--nested', action='store_true',
                                   help='Create nested folder structure based on page names')
    doc_export_parser.set_defaults(func=doc_export_command)

    # Doc import
    doc_import_parser = subparsers.add_parser(
        'doc_import',
        aliases=['di'],
        help='Import markdown files to create docs',
        description='Import local markdown files to create ClickUp Docs and pages.',
        epilog='''Tips:
  • Import from directory: cum di current ./docs --doc-name "My Doc"
  • Recursive import: cum di current ./docs --recursive --nested
  • Each .md file becomes a page
  • Use --nested to preserve folder structure in page names
  • Great for migrating documentation to ClickUp'''
    )
    doc_import_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    doc_import_parser.add_argument('input_dir', help='Input directory containing markdown files')
    doc_import_parser.add_argument('--doc-name', dest='doc_name',
                                   help='Doc name (for importing single doc from directory)')
    doc_import_parser.add_argument('--nested', action='store_true',
                                   help='Preserve nested folder structure in page names')
    doc_import_parser.add_argument('--recursive', action='store_true',
                                   help='Recursively find markdown files in subdirectories')
    doc_import_parser.set_defaults(func=doc_import_command)

    # Page list
    page_list_parser = subparsers.add_parser(
        'page_list',
        aliases=['pl'],
        help='List all pages in a doc',
        description='Display all pages within a specific ClickUp Doc.',
        epilog='''Tips:
  • List pages: cum pl current <doc_id>
  • Shows page IDs and names
  • Use doc_get for more detail including content previews
  • Page IDs needed for page_update command
  • Docs can contain unlimited pages'''
    )
    page_list_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    page_list_parser.add_argument('doc_id', help='Doc ID')
    page_list_parser.set_defaults(func=page_list_command)

    # Page create
    page_create_parser = subparsers.add_parser(
        'page_create',
        aliases=['pc'],
        help='Create a new page in a doc',
        description='Add a new page to an existing ClickUp Doc with optional content.',
        epilog='''Tips:
  • Create empty page: cum pc current <doc_id> --name "New Page"
  • Create with content: cum pc current <doc_id> --name "Page" --content "# Content"
  • Content supports markdown formatting
  • Pages appear in doc navigation
  • Use page_update to modify after creation'''
    )
    page_create_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    page_create_parser.add_argument('doc_id', help='Doc ID')
    page_create_parser.add_argument('--name', required=True, help='Page name')
    page_create_parser.add_argument('--content', help='Page content (markdown)')
    page_create_parser.set_defaults(func=page_create_command)

    # Page update
    page_update_parser = subparsers.add_parser(
        'page_update',
        aliases=['pu'],
        help='Update a page in a doc',
        description='Modify the name or content of an existing page in a ClickUp Doc.',
        epilog='''Tips:
  • Update page name: cum pu current <doc_id> <page_id> --name "New Name"
  • Update content: cum pu current <doc_id> <page_id> --content "New content"
  • Update both: cum pu current <doc_id> <page_id> --name "New" --content "Updated"
  • Find page IDs with page_list
  • Same as doc_update (both update pages)'''
    )
    page_update_parser.add_argument('workspace_id', help='Workspace/team ID (or "current")')
    page_update_parser.add_argument('doc_id', help='Doc ID')
    page_update_parser.add_argument('page_id', help='Page ID')
    page_update_parser.add_argument('--name', help='New page name')
    page_update_parser.add_argument('--content', help='New page content (markdown)')
    page_update_parser.set_defaults(func=page_update_command)
