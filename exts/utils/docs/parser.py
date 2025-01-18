"A parser that can extract "

from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin

_YELLOW_ANSI = '\u001b[38;2;238;210;2m'
_WHITE_ANSI  = '\u001b[37m'

def html_to_markdown(content: Tag, website_url: str, url: str) -> str:
    description = content.find(name = 'p')
    codeblock_div = content.find(
        name = 'div',
        attrs = {'class': 'highlight'},
        recursive = True
    )

    result = ""
    superscripts = dict(zip("123456789", "¹²³⁴⁵⁶⁷⁸⁹"))

    if description:
        for child in description.children:
            if isinstance(child, NavigableString):
                result += str(child)
            
            elif isinstance(child, Tag):
                match child.name:
                    case 'a':
                        if child.attrs["href"].startswith('#'):
                            absolute_url = website_url + child.attrs["href"]
                        else:
                            absolute_url = urljoin(website_url, child.attrs["href"])
                        
                        result += f"[`{child.get_text()}`]({absolute_url})"
                    
                    case 'code' | 'kbd':
                        result += f"`{child.get_text()}`"
                    
                    case 'em' | 'i':
                        result += f"_{child.get_text()}_"
                    
                    case 'strong' | 'b':
                        result += f"**{child.get_text()}**"
                    
                    case 'span': pass

                    case 'abbr':
                        result += f"{child.get_text()} ({child.attrs["title"]})"
                    
                    case 'sup':
                        result += ''.join(
                            superscripts.get(n, f'^{n}')
                            for n in child.get_text()
                        )
                
                    case _:
                        print(f"{_YELLOW_ANSI}WARN:{_WHITE_ANSI} Could not resolve tag '{child}' in url '{url}'.")
            
            else:
                print(f"{_YELLOW_ANSI}WARN:{_WHITE_ANSI} Could not resolve child '{child}' in url '{url}'.")
    
    # Remove strange whitespace
    result = result.replace('  ', ' ').replace('\n', ' ')

    if codeblock_div:
        codeblock = codeblock_div.find(
            name = "pre",
            recursive = True
        )

        result += f"\n```py\n{codeblock.get_text().strip()}\n```"
    
    # Something strange to do with encodings producing the wrong outputs
    return result

# ===============================================================================================================

from functools import lru_cache

@lru_cache(maxsize = 1024)
def get_soup_instance(content: str) -> BeautifulSoup:
    return BeautifulSoup(content, features = "lxml")

def get_usage_and_description(
    local_parent_filepath: str,
    relative_filepath: str,
    website_url: str,
    method: str,
    codeblock_language: str
) -> tuple[str, str]:
    "Return a named tuple of a command's usage, then description, in that order."

    with open(
        local_parent_filepath
      + relative_filepath,
      
        encoding = 'utf-8',
        errors = "ignore"
    ) as f:
        content = f.read()

    bs = get_soup_instance(content)

    title = bs.find(attrs = {'id': method})

    return (
        # Usage
        f"```{codeblock_language}\n{title.get_text().strip('\nÂ¶')}\n```",

        # Description
        html_to_markdown(
            title.parent,
            url = local_parent_filepath + relative_filepath,
            website_url = website_url + relative_filepath
        )
    )