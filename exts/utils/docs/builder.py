"A module with a `Builder` class that can load and store documentation."

from .parser import get_usage_and_description
from re import search
from sqlite3 import connect, Row
from time import time
from zlib import decompress

class Builder:
    """
    A class with the ability to build and store documentation
    previously generated with Sphinx.
    """
    
    @staticmethod
    def _understand_line(line: str) -> tuple[str, str, str, int, str, str]:
        """
        Dissect a given `line` into its corresponding parts, as per
        this pattern:

        ```yml
        {name} {domain}:{role} {priority} {uri} {dispname}
        ```

        This returns a tuple of 5 strings and 1 integer, as `priority`
        is internally converted to an integer before returning.

        Parameters
        ----------
        line: `str`
            the line to dissect.
        
        Returns
        -------
        `tuple[str, str, str, int, str, str]`
            a tuple of the line's `name`, `domain`, `role`, `priority`, `uri`, `dispname`
        """
        
        # Regex for finding a domain-role pair
        result = search(r' \w+:[\w-]+', line)
        
        # The name is everything before the domain-role pair.
        # This could be more than one word, which is why we
        # have to use this approach.
        name = line[ : result.start()].strip()

        # Get the substring representing the match
        domain_and_role_text = result.string[
            result.start()
          : result.end()
        ]
        
        # Get the domain and role
        domain, role = domain_and_role_text.strip().split(':')
        
        # Get everything right of the domain-role pair
        other_tokens = line[result.end() + 1 : ].split(' ')

        priority = int(other_tokens[0])

        # Make the URI valid instead of a template
        uri = other_tokens[1].replace('$', name)

        # Everything else is the dispname
        dispname = ' '.join(other_tokens[2:])

        return name, domain, role, priority, uri, dispname

    def __init__(self):
        """
        Create an instance of `Builder` that automatically establishes a connection with the `docs.sql` database.

        If the database is not found, a fresh one is created in the same directory as this file, regardless of
        current working directory.
        """
        
        current_directory = __file__.rsplit('\\', maxsplit = 1)[0]

        self.conn = connect(f"{current_directory}/docs.sql", autocommit = True)
        self.conn.row_factory = Row
    
    @staticmethod
    def _to_human_duration(seconds: float) -> str:
        """
        Translate a number of total seconds into a more readable format of `_d _h _m _s`.

        Parameters
        ----------
        seconds: `float`
            the number of seconds to translate.
        """
        
        if seconds < 1:
            return f'{seconds:.1f}s'
        
        _real_seconds = seconds % 60
        _remaining_seconds = int(seconds) % 60

        total_seconds = int(seconds)

        units = {
            86400: 'd',
            3600: 'h',
            60: 'm',
            1: 's'
        }

        result = []

        for amount, unit in units.items():
            value, total_seconds = divmod(total_seconds, amount)

            if value > 0:
                result.append(f"{value}{unit}")
        
        diff = round(_real_seconds - _remaining_seconds, 1)

        if 's' in result[-1]:
            secs = int(result[-1][:-1])
            result[-1] = f"{secs + diff}s"
        else:
            result.append(f"{diff}s")
        
        return ' '.join(result)
    
    def build(
        self,
        *,
        inv_path: str,
        base_url: str,
        web_url: str,
        table_name: str,
        notify_every: int = 1000
    ) -> None:
        """
        Export a Sphinx `.inv` file, along with the corresponding documentation in HTML,
        into a named SQLite table in the database `./data.sql`.

        This will print status updates for how the operation is progressing.

        Parameters
        ----------
        inv_path: `str`
            the path of the `.inv` file.
        
        base_url: `str`
            the local parent directory holding the HTML files.
        
        web_url: `str`
            the base URL that can be accessed over the internet (eg. `https://docs.python.org/3/` for Python docs)
        
        table_name: `str`
            the name of the SQLite table for this information to be inserted into.
        
        notify_every: `int`
            the amount of rows that should be considered before a status update is posted. Default is 1,000.
        """
        
        self.conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')

        self.conn.execute(
           f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                role TEXT NOT NULL,
                priority INT NOT NULL,
                uri TEXT NOT NULL,
                dispname TEXT NOT NULL,

                link TEXT AS ("{web_url}" || uri),

                usage TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )

        # Open the inventory file
        with open(inv_path, 'rb') as f:
            # Skip the headings
            for _ in range(4):
                f.readline()
            
            # Decompress, decode, and split the document into lines
            content = decompress(f.read()).decode().splitlines()
        
        CYAN = "\u001b[38;2;80;253;254m"
        GREY = "\u001b[38;2;24;24;24m"
        PURPLE = "\u001b[38;2;90;50;168m"
        WHITE = "\u001b[37m"

        print('=' * 75)
        print(f"Beginning build... => {CYAN}{table_name}  {PURPLE}({len(content):,} entries){WHITE}")
        print('=' * 75)

        t0 = time() # Timestamp of when the process started
        t1 = time() # Timestamp of when the most recent X entries were completed
        
        for pos, line in enumerate(content):
            # Every X entries completed, notify the user and tell
            # the time it took to complete a row.
            if (pos + 1) % notify_every == 0:
                print(f"Finished {pos + 1:,}/{len(content):,} entries. {GREY}(in {Builder._to_human_duration(time() - t1)}){WHITE}")
                t1 = time()
            
            # Dissect the line into its corresponding parts
            name, domain, role, priority, uri, dispname = Builder._understand_line(line)

            if priority == -1:
                continue

            usage, description = "", ""

            if '#' in uri:
                # Get the path to the HTML file
                # and the section to check.
                path, section = uri.split('#')

                # Get the usage of the command and its description
                # from the corresponding HTML document.
                usage, description = get_usage_and_description(
                    local_parent_filepath = base_url,
                    relative_filepath = path,
                    website_url = web_url,
                    method = section,
                    codeblock_language = domain
                )

            # Insert it into the database
            self.conn.execute(
               f"""
                INSERT INTO "{table_name}" (
                    name,
                    domain,
                    role,
                    priority,
                    uri,
                    dispname,
                    usage,
                    description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    domain,
                    role,
                    priority,
                    uri,
                    dispname,
                    usage,
                    description
                )
            )
        
        time_taken = time() - t0

        print('=' * 75)
        print(f"Finished building! => {CYAN}{table_name}  {GREY}(in {Builder._to_human_duration(time_taken)})  {PURPLE}({Builder._to_human_duration(time_taken / len(content))} / line){WHITE}")
        print('=' * 75)