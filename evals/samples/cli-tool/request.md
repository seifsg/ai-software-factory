Add a command-line tool `wordcount.py` to this project. Python 3, standard library only.

1. `python wordcount.py FILE` prints the file's line, word and character counts on one line, as `lines words chars` separated by single spaces. Words are separated by whitespace.
2. `python wordcount.py --top N FILE` prints that line, then the N most frequent words, one `word count` per line, most frequent first, ties in alphabetical order. Words compare case-insensitively and print in lowercase.
3. A file that does not exist prints an error naming the file to stderr, without a traceback, and exits with code 2.
