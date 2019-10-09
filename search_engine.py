import os
import shelve
import indexer
from indexer import Position_with_lines
import re
from tokenizator_generator_krupina import Tokenizer


class ContextWindow(object):
    """This class stores information about context windows

    """

    def __init__(self, positions, line, beginning, end):
        """This method creates an instance of ContextWindow class

        @param positions: a list of positions of the words we search for
        @param line: the text of the line with the word
        @param beginning: position of the first character of the context window
        @param end: position after the last character of the context window

        """
        self.positions = positions
        self.line = line
        self.beginning = beginning
        self.end = end

    @classmethod
    def get_from_file(cls, filename: str, position: Position_with_lines, context_size=3):
        """This method yields contexts from a file

        @param filename: the name of the file we are working with
        @param position: position of the word which contexts we are trying to find 
        @param context_size: size of the context window

        """
        if not (isinstance(filename, str) and isinstance(position, Position_with_lines)
                and isinstance(context_size, int)):
            raise ValueError(filename, position, context_size)

        with open(filename) as f:
            for i, line in enumerate(f):
                if i == position.line:
                    break
        if i != position.line:
            raise ValueError('Wrong line number')

        line = line.strip("\n")
        positions = [position]

        tokenizer_1 = Tokenizer()

        right = [token.word for i, token in enumerate(tokenizer_1.generate_alpha_and_digits(line[position.end:]))
                 if i < context_size]
        left = [token.word for i, token in
                enumerate(tokenizer_1.generate_alpha_and_digits(line[:position.beginning][::-1])) if i < context_size]

        sum_len_left = sum(map(len, left[-context_size:])) + context_size + 1
        sum_len_right = sum(map(len, right[:context_size])) + context_size + 1

        beginning = max(0, position.beginning - sum_len_left)
        end = min(len(line), position.end + sum_len_right)
        return cls(positions, line, beginning, end)

    def check_crossing(self, con):
        """This method is meant to find if there is any overlapping of the context windows

        @param con: the context we are checking

        """
        return (self.beginning <= con.end and
                self.end >= con.beginning and
                con.line == self.line)

    def join_contexts(self, con):
        """A method for combining overlapping contexts

        @param con: the context that is to be combined with

        """
        for position in con.positions:
            if position not in self.positions:
                self.positions.append(position)
        self.beginning = min(self.beginning, con.beginning)
        self.end = max(self.end, con.end)

    def expand_context(self):
        """Expanding the boundaries of the context window to a sentence

        """
        end_sent = re.compile(r'[.!?]\s[A-ZА-Яa-zа-я]')
        beg_sent = re.compile(r'[A-ZА-Яa-zа-я]\s[.!?]')
        max_right = max([pos.end for pos in self.positions])
        min_left = min([pos.beginning for pos in self.positions])
        right = self.line[max_right:]
        left = self.line[::-1][-min_left:]
        first_obj = end_sent.search(right)
        last_obj = beg_sent.search(left)

        if left:
            if last_obj:
                self.beginning = len(left) - last_obj.end() + 2
            else:
                self.beginning = 0
        if right:
            if first_obj:
                self.end = max_right + first_obj.start() + 1
            else:
                self.end = len(self.line)

    def highlight(self):
        """Highlights query words in the output

        """
        highlighted = self.line[self.beginning:self.end]
        for pos in self.positions[::-1]:
            end = pos.end - self.beginning
            start = pos.beginning - self.beginning
            highlighted = highlighted[:end] + '</B>' + highlighted[end:]
            highlighted = highlighted[:start] + '<B>' + highlighted[start:]
        return highlighted

    def __eq__(self, con):
        """Checking if two context windows are equal

        @param con: the context window to compare

        """
        return ((self.positions == con.position) and
                (self.line == con.line) and
                (self.beginning == con.beginning) and
                (self.end == con.end))

    def __repr__(self):
        return self.line[self.beginning:self.end]


class SearchEngine(object):
    """Searching engine for finding certain tokens or groups of tokens in a database

    """

    def __init__(self, database):
        """Creates an instance of the class SearchEngine

        @param database: the name of the database that is going to be used for searching in it

        """
        self.database = shelve.open(database, writeback=True)

    def single_token_search(self, query):
        """A method of searching for only one token

        @param query: the word that is to be searched for

        """
        if not isinstance(query, str):
            raise TypeError
        if query not in self.database:
            return {}
        if query == "":
            raise ValueError
        return self.database[query]

    def multiple_tokens_search(self, query):
        """A method of searching for several tokens

        @param query: two or more tokens that are to be searched for

        """
        if not isinstance(query, str):
            raise TypeError
        if query == "":
            raise ValueError
        tokenizer = Tokenizer()
        search_tokens = list(tokenizer.generate_alpha_and_digits(query))
        search_results = []
        for token in search_tokens:
            if token.word not in self.database:
                return {}
            search_results.append(self.single_token_search(token.word))
        files = set(search_results[0])
        for result in search_results[1:]:
            files &= set(result)
        final_result = {}
        for file in files:
            for result in search_results:
                final_result[file] = final_result.setdefault(file, []) + result[file]
        return final_result

    def get_window(self, input_dict, context_size):
        """This method creates a dictionary of files and contexts

        @param input_dict: a dictionary of files and positions
        @param context_size: size of the output context windows

        """
        if not (isinstance(input_dict, dict) and
                isinstance(context_size, int)):
            raise ValueError

        contexts_dict = {}
        for f, positions in input_dict.items():
            for position in positions:
                context = ContextWindow.get_from_file(f, position, context_size)
                contexts_dict.setdefault(f, []).append(context)

        joined_contexts_dict = self.join_windows(contexts_dict)

        return joined_contexts_dict

    def join_windows(self, input_dict):
        """Combine overlapping windows in a dictionary of files and context windows

        @param input_dict: a dictionary to combine

        """
        for k in input_dict:
            input_dict[k] = sorted(input_dict[k], key=lambda cont: cont.beginning)
        contexts_dict = {}
        null_cont = ContextWindow([], "", 0, 0)
        for f, contexts in input_dict.items():
            previous_context = null_cont
            for context in contexts:
                if previous_context.check_crossing(context):
                    previous_context.join_contexts(context)
                else:
                    if previous_context is not null_cont:
                        contexts_dict.setdefault(f, []).append(previous_context)
                    previous_context = context
            contexts_dict.setdefault(f, []).append(previous_context)

        return contexts_dict

    def search_to_context(self, query, context_size=3):
        """Searching for a query word. The result is a context window of a certain size with
        the query word in the middle

        """
        positions_dict = self.multiple_tokens_search(query)
        context_dict = self.get_window(positions_dict, context_size)
        return context_dict

    def search_to_sentence(self, query, context_size=3):
        """This method is similar to the previous one, but now contexts windows are full sentences

        """
        context_dict = self.search_to_context(query, context_size)
        for contexts in context_dict.values():
            for context in contexts:
                context.expand_context()
        sentence_dict = self.join_windows(context_dict)
        return sentence_dict

    def search_to_highlight(self, query, context_size=3):
        """Also searching in the database, but in the result query words are highlighted

        """
        sentence_dict = self.search_to_context(query, context_size)
        quote_dict = {}
        for f, conts in sentence_dict.items():
            for cont in conts:
                quote_dict.setdefault(f, []).append(cont.highlight())
        return quote_dict

    def close_database(self):
        self.database.close()
        for filename in os.listdir(os.getcwd()):
            if filename.startswith('database.'):
                os.remove(filename)
            if filename.startswith('text'):
                os.remove(filename)


def entering():
    file_name, query = input('Enter the name of file you want to tokenize: \n'), \
                       input('Enter the query you want to find: \n')
    function = int(input('Select the function you want to apply to the file (enter the number 1-4):\n'
                         '1 - search several words\n'
                         '2 - search to sentence\n'
                         '3 - search to highlight\n'
                         '4 - exit\n'
                         ))
    return file_name, query, function


def main():
    indexing = indexer.Indexer('database')
    file_name, query, function = entering()
    indexing.indexing_with_lines(file_name)
    searching = SearchEngine('database')

    result = None
    if function == 1:
        result = searching.multiple_tokens_search(query)
    elif function == 2:
        context_size = int(input('Enter the context size to search for:\n'))
        result = searching.search_to_sentence(query, context_size)
    elif function == 3:
        context_size = int(input('Enter the context size to search for:\n'))
        result = searching.search_to_highlight(query, context_size)
    elif function == 4:
        exit()
    else:
        print('You entered a wrong function number, try again')
        entering()

    with open('result.txt', 'w') as result_file:
        for key in result:
            result_file.write(key + ':\n')
            for el in result[key]:
                result_file.write(str(el) + '\n')
            result_file.write('\n')

    del searching
    for filename in os.listdir(os.getcwd()):
        if filename == 'database' or filename.startswith('database.'):
            os.remove(filename)


if __name__ == '__main__':
    main()
