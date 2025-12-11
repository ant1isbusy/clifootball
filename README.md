# cli football analysis [DEPRECATED]
This simple tool allows you to check on your favorite teams and players inside the terminal. Made with python and sqlite.

In this way you can quickly check the latest results, league tables, top scorers, etc. without ever leaving the terminal :)

A preview of the program:

![missing](preview.png)

**Requirements:** Two python libraries are needed, which can simply be installed with:
```bash
pip install -r requirements.txt
```

If you have a particular football club you like to follow, I recommend setting up a shortcut in your .zshrc or .bashrc file. This way you can quickly check on your favorite team by typing a simple command in the terminal.

I for example have the following alias in my zshrc file:

```bash
alias prem='python3 ~/path/query_fav.py "EPL" "Arsenal"'
```
Which prints the league table with Arsenal highlighted in the terminal.

Currently the top 4 leagues in Europe are supported and can be passed to the query_fav.py script with these keywords:
```EPL, La_liga, Bundesliga, Serie_a```

Scraped sources are deprecated.
