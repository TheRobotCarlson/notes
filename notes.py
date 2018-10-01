import os
import sys
import click

import curses

menu_options = []
menu_question = ""
chosen_option = ""

class NotesRepo(object):

    def __init__(self, home, private, git_sync):
        self.home = home
        self.private = private
        self.config = {}
        self.git_sync = git_sync
        self.verbose = False

    def set_config(self, key, value):
        self.config[key] = value
        if self.verbose:
            click.echo('  config[%s] = %s' % (key, value), file=sys.stderr)

    def path(self, sub_dir=None):
        path = self.home

        if self.private:
            path += "/private"
        else:
            path += "/public"

        if sub_dir is not None:
            path += "/" + sub_dir
        
        return path

    def get_files(self, sub_dir=None):
        path_str = self.path(sub_dir=sub_dir)
        paths = {}
        excludes = [".git"]
        for root, directories, filenames in os.walk(path_str, topdown=True):
            directories[:] = [d for d in directories if d not in excludes] 
            for filename in filenames: 
                if filename.endswith(('.md')):
                    full_path = os.path.join(root, filename)
                    if filename in paths:
                        paths[filename].append(full_path)
                    else:
                        paths[filename] = [full_path]
        

        return paths

    def sync(self):
        private = self.private

        self.private = False
        os.system('%s %s' % (self.git_sync, self.path()))
 
        self.private = True
        os.system('%s %s' % (self.git_sync, self.path()))

        self.private = private


    def __repr__(self):
        return '<Repo %r>' % self.home


pass_repo = click.make_pass_decorator(NotesRepo)


@click.group()
@click.option('--notes-home', envvar='NOTES_HOME', default=os.path.expanduser('~/notes'),
              metavar='PATH', help='Changes the notes folder location.')
@click.option('--git-sync', '-g', default=os.path.expanduser('~/notes/notes_sync.sh'))
@click.option('--config', nargs=2, multiple=True,
              metavar='KEY VALUE', help='Overrides a config key/value pair.')
@click.option('--verbose', '-v', is_flag=True,
              help='Enables verbose mode.')
@click.option('--private', '-p', is_flag=True, help='Put in private repo.')
@click.version_option('1.0')
@click.pass_context
def cli(ctx, notes_home, git_sync, config, verbose, private):
    """Notes is a command line tool for quick commandline notetaking. Designed to be
    quick and work with git.
    """
    # Create a repo object and remember it as as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @pass_repo decorator.
    ctx.obj = NotesRepo(os.path.abspath(notes_home), private, git_sync)
    ctx.obj.verbose = verbose
    for key, value in config:
        ctx.obj.set_config(key, value)


@cli.command("list")
@click.argument('category', required=False, type=click.Path())
@click.option('--show-path', '-a', is_flag=True)
@click.option('--show-category', '-c', is_flag=True)
@click.option('--tag', '-t', default='ROOT',
              help='Filter based on tag')           
@pass_repo
def list_files(repo, category, show_path, show_category, tag):
    """Lists Notes.
    Recursively lists notes, either from the root category or a chosen category.

    """
    paths = repo.get_files(category)

    for entry in paths.keys():
        for item in paths[entry]:
            if show_path:
                print(item)
            elif show_category:
                print(item.replace(repo.home, ""))
            else:
                print(entry)

@cli.command("new")
@click.argument("note")
@pass_repo
def create_note(repo, note):
    """Creates a note.
    This will let a user create a note.
    """
    filename = note + ".md"
    path = repo.path(filename)

    if not os.path.isfile(os.path.dirname(path)):
        os.system('mkdir %s' % (os.path.dirname(path)))

    os.system('%s %s' % (os.getenv('EDITOR'), path))

@cli.command("open")
@click.argument("note")
@pass_repo
def open_note(repo, note):
    """Opens a note.
    This will let a user open a note.
    """
    if ".md" not in note:
        note = note + ".md"
    
    dir_pieces = note.split("/")
    filename = dir_pieces[-1]
    paths = repo.get_files().get(filename, [])

    if len(paths) == 0:
        print("File does not exist")
        return
    elif len(paths) == 1:
        path = paths[0]
    else:
        temp_paths = []
        for p in paths:
            if note in p:
                temp_paths.append(p)
        if len(temp_paths) > 1:
            path = create_menu("Which file do you want?", temp_paths)
        elif len(temp_paths) == 1:
            path = temp_paths[0]
        else:
            print("File isn't in the category you gave.")

    os.system('%s %s' % (os.getenv('EDITOR'), path))
    

@cli.command()
@click.argument("note")
@click.confirmation_option()
@pass_repo
def delete(repo, note):
    """Deletes a note.
    This will delete a note.
    """
    filename = note + ".md"
    dir_pieces = filename.split("/")
    name = dir_pieces[-1]
    paths = repo.get_files().get(name, [])

    if len(paths) == 0:
        print("File does not exist")
        return
    elif len(paths) == 1:
        path = paths[0]
    else:
        temp_paths = []
        for p in paths:
            if filename in p:
                temp_paths.append(p)
        if len(temp_paths) > 1:
            path = create_menu("Which file do you want?", temp_paths)
        elif len(temp_paths) == 1:
            path = temp_paths[0]
        else:
            print("File isn't in the category you gave.")

    os.system('rm %s' % (path))

@cli.command()
@pass_repo
def sync(repo):
    """Syncs notes.
    This will sync your notes.
    """
    repo.sync()

def create_menu(question, options):
    global menu_question
    global menu_options

    menu_question = question
    menu_options = options
    curses.wrapper(menu)

    return chosen_option

def menu(stdscr):
    global chosen_option
    attributes = {}
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    attributes['normal'] = curses.color_pair(1)

    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    attributes['highlighted'] = curses.color_pair(2)

    c = 0  # last character read
    option = 0  # the current option that is marked
    while c != 10:  # Enter in ascii
        stdscr.erase()
        stdscr.addstr(menu_question + "\n", curses.A_UNDERLINE)
        for i in range(len(menu_options)):
            if i == option:
                attr = attributes['highlighted']
            else:
                attr = attributes['normal']
            stdscr.addstr("{0}. ".format(i + 1))
            stdscr.addstr(menu_options[i] + '\n', attr)
        c = stdscr.getch()
        if c == curses.KEY_UP and option > 0:
            option -= 1
        elif c == curses.KEY_DOWN and option < len(menu_options) - 1:
            option += 1

    chosen_option = menu_options[option]
    # stdscr.getch()

if __name__ == '__main__':
    cli()