from indexer import Indexer 
import os
import shelve


def main():
    for filename in os.listdir(os.getcwd()):
        if filename == 'database' or filename.startswith('database.'):
            os.remove(filename)

    indexator = Indexer('database') 
    indexator.indexing_with_lines('tolstoy1.txt')

    indexator = Indexer('database')
    indexator.indexing_with_lines('tolstoy2.txt')

    indexator = Indexer('database')
    indexator.indexing_with_lines('tolstoy3.txt')

    indexator = Indexer('database')
    indexator.indexing_with_lines('tolstoy4.txt')

    database = shelve.open('database')
    print(dict(database))


main()
