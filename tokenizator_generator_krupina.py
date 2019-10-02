"""This tokenizer is meant to find tokens in the text given

Token is a word which in this case means a sequence of alphabetical symbols

"""
from unicodedata import category


class Token(object):
    """Define a class Token which is going to contain all the tokens we are about to find

    """
    
    def __init__(self, position, word):
        """ Initializes tokens

        @param position: position of the first letter of a word in a sequence given
        @param word: a sequence of alphabetical symbols forming a word itself

        """
        self.position = position
        self.word = word


class TypeToken(object):
    
    def __init__(self, position, word, typ):
        """ Initializes tokens, but now we also get their types

        @param position: position of the first letter of a word in a sequence given
        @param word: a sequence of alphabetical symbols forming a word itself
        @param typ: the type of the token. It can be alphabetic (a), digit (d), space (s), punctuation (p), other (o)

        """
        self.position = position
        self.word = word
        self.typ = typ


class Tokenizer(object):
    """Create a class which contains a function of tokenizing

    """
    
    def tokenize(self, given):
        """The function "tokenize" searches for words(tokens) in our sequence

        @param given: a sequence of alphabetical and non-alphabetical symbols
        @return: a list of tokens

        """
        if not isinstance(given,str):
            raise ValueError('Value error')

        if not given:
            return []

        i, s = 0, None
        tokens = []   # Create an empty list of tokens which it to be fulfilled later
        # The index can assume either a value of -1 or the value of the position of the symbol 
        index = -1
          
        for i, s in enumerate(given):
            # Check if the symbol in question is the end of a word
            if index > -1 and not s.isalpha():
                # If so, add the token to the list of tokens
                tokens.append(Token(index, given[index:i]))  
                index = -1
            # Check whether the symbol in question is the beginning of a word
            if index == -1 and s.isalpha(): 
                index = i
        # Check the last symbol of the sequence to see whether it is the end of a word
        # If so, add this word to our list of tokens
        if s.isalpha():
            tokens.append(Token(index, given[index:i+1]))
        return tokens

    def generator_tokenizer(self, given):
        """The function "generator_tokenizer" searches for words(tokens) in our sequence

        @param given: a sequence of alphabetical and non-alphabetical symbols
        @return: a list of tokens

        """
        
        if not isinstance(given,str):
            raise ValueError('Value error')

        if not given:
            return

        # The index can assume either a value of -1 or the value of the position of the symbol
        token = Token(0, None)
        index = -1
        s = None
        for i, s in enumerate(given):
            # Check if the symbol in question is the end of a word
            if index > -1 and not s.isalpha():
                token = (Token(index, given[index:i]))  
                index = -1
                yield token
            # Check whether the symbol in question is the beginning of a word
            if index == -1 and s.isalpha(): 
                index = i
        # Check the last symbol of the sequence to see whether it is the end of a word
        if s.isalpha():
            token = (Token(index, given[index:i+1]))

        yield token

    @staticmethod
    def _get_type(c):
        """This method gets the type of each character in a sequence

        @param c: the character which type is to be identified
        @return: type of the character: alphabetical (a), digit (d), space (s), punctuation (p), other (o)

        """
        ch_category = category(c)

        if ch_category [0] == "L":
            return "a"      # alphabetical
        elif ch_category [0] == "N":
            return "d"      # digit
        elif ch_category [0] == "Z":
            return "s"       # space or separator
        elif ch_category [0] == "P":
            return "p"       # punctuation
        else:
            return "o"       # other

    def generator_with_types(self, given):
        """This method also divides the sequence of symbols into tokens, but now we also get the type of each token

        @param given: a sequence of alphabetical and non-alphabetical symbols
        @return: a list of tokens

        """
        token = TypeToken(None, None, None)
        p_token_type = ""
        index = 0
        for i, c in enumerate(given):
            c_token_type = self._get_type(c)
            if c_token_type != p_token_type and i>0:
                token = TypeToken(index, given[index:i], p_token_type)
                yield token
                index = i
            p_token_type = c_token_type
            token = TypeToken(index, given[index:i+1], p_token_type)        
        yield token

    def tokenize_with_types(self, given):
        return list(self.generator_with_types(given))
    
    def generate_alpha_and_digits(self, given):
        for token in self.generator_with_types(given):
            if (token.typ == 'a') or (token.typ == 'd'):
                yield token


if __name__ == '__main__':

    given = "Привет, я нормальное предложение, а ты?"

    words = Tokenizer().tokenize(given)     # Apply our function of tokenizing to a text given

    for token in words:
        print(token.word, token.position)   # Print each token found and its position

    generator_words = Tokenizer().generator_tokenizer(given)    # Apply our function of generating to a text given

    for token in generator_words:
        print(token.word, token.position)   # Print each element found and its position

    words_types_g = Tokenizer()

    tokens = list(words_types_g.generator_with_types(given))

    for token in tokens:
        print(token.word, token.position, token.typ)
