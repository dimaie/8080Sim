class Position:
    def __init__(self, line, col):
        self.line = line
        self.col = col

    def __str__(self):
        return f"{self.line}:{self.col}"


class ParseError(Exception):
    def __init__(self, message, pos):
        super().__init__(message)
        self.pos = pos

    def __str__(self):
        return f"Parse error at {self.pos}: {self.args[0]}"


class Lexer:
    def __init__(self, buf):
        self.pos = 0
        self.buf = buf
        self.lineCount = 1
        self.lastNewlinePos = 0
        self._ops = {':', ',', '[', ']'}

    def token(self):
        self._skipNonTokens()
        if self.pos >= len(self.buf):
            return None

        if self.buf[self.pos] == ';':
            start = self.pos
            endpos = self.pos + 1
            while endpos < len(self.buf) and not self._isNewline(self.buf[endpos]):
                endpos += 1
            raw_val = self.buf[start:endpos]
            tok = {
                'name': 'COMMENT',
                'value': raw_val,
                'raw': raw_val,
                'pos': self._position()
            }
            self.pos = endpos
            return tok

        c = self.buf[self.pos]
        if self._isNewline(c):
            tok = {'name': 'NEWLINE', 'value': c, 'raw': c, 'pos': self._position()}
            self._skipNewlines()
            return tok

        if c in self._ops:
            tok = {'name': c, 'value': c, 'raw': c, 'pos': self._position()}
            self.pos += 1
            return tok
        else:
            if self._isAlphaNum(c):
                return self._id()
            elif c == "'":
                return self._string()
            else:
                raise ParseError("invalid token", self._position())

    def _id(self):
        endpos = self.pos + 1
        while endpos < len(self.buf) and self._isAlphaNum(self.buf[endpos]):
            endpos += 1

        raw_val = self.buf[self.pos:endpos]
        if endpos < len(self.buf) and self.buf[endpos] == ':':
            raw_val += ':'
            tok = {
                'name': 'LABEL',
                'value': self.buf[self.pos:endpos],
                'raw': raw_val,
                'pos': self._position()
            }
            self.pos = endpos + 1
            return tok
        else:
            val_lower = raw_val.lower()
            is_number = False
            if val_lower.endswith('h') and val_lower[:-1] and all(c in '0123456789abcdef' for c in val_lower[:-1]):
                is_number = True
            elif val_lower.endswith('b') and val_lower[:-1] and all(c in '01' for c in val_lower[:-1]):
                is_number = True
            elif val_lower.isdecimal():
                is_number = True

            tok = {
                'name': 'NUMBER' if is_number else 'ID',
                'value': raw_val,
                'raw': raw_val,
                'pos': self._position()
            }
            self.pos = endpos
            return tok

    def _string(self):
        end = self.buf.find("'", self.pos + 1)
        if end < 0:
            raise ParseError("unterminated quote", self._position())
        else:
            tok = {
                'name': 'STRING',
                # We return it as a list of characters to mimic the JS Array structure 
                # needed later by the `db` instruction in the Assembler.
                'value': list(self.buf[self.pos + 1:end]),
                'raw': self.buf[self.pos:end + 1],
                'pos': self._position()
            }
            self.pos = end + 1
            return tok

    def _skipNonTokens(self):
        while self.pos < len(self.buf):
            c = self.buf[self.pos]
            if c == ' ' or c == '\t':
                self.pos += 1
            else:
                break

    def _isNewline(self, c):
        return c == '\r' or c == '\n'

    def _skipNewlines(self):
        while self.pos < len(self.buf):
            c = self.buf[self.pos]
            if self._isNewline(c):
                self.lineCount += 1
                self.lastNewlinePos = self.pos
                self.pos += 1
            else:
                break

    def _isAlphaNum(self, c):
        return ('a' <= c <= 'z') or \
               ('A' <= c <= 'Z') or \
               ('0' <= c <= '9') or \
               c in ('.', '_', '$')

    def _position(self):
        return Position(self.lineCount, self.pos - self.lastNewlinePos)


class Parser:
    def __init__(self):
        self.tokens = []

    def parse(self, s):
        result = []
        lexer = Lexer(s)
        self.tokens = []

        def get_next_tok():
            while True:
                tok = lexer.token()
                if tok is not None:
                    self.tokens.append(tok)
                if tok is None or tok['name'] != 'COMMENT':
                    return tok

        while True:
            curTok = get_next_tok()

            while curTok is not None and curTok['name'] == 'NEWLINE':
                curTok = get_next_tok()

            if curTok is None:
                return result

            labelTok = None
            if curTok['name'] == 'LABEL':
                labelTok = curTok
                curTok = get_next_tok()

            if curTok is None or curTok['name'] == 'NEWLINE':
                result.append({
                    'label': labelTok['value'],
                    'instr': None,
                    'args': [],
                    'pos': labelTok['pos']
                })
                continue

            if curTok['name'] != 'ID':
                self._parseError(curTok['pos'], f"want ID; got \"{curTok['value']}\"")

            idTok = curTok
            args = []

            curTok = get_next_tok()

            while curTok is not None and curTok['name'] != 'NEWLINE':
                if curTok['name'] in ('ID', 'STRING', 'NUMBER'):
                    args.append(curTok['value'])
                else:
                    self._parseError(curTok['pos'], f"want arg; got \"{curTok['value']}\"")

                curTok = get_next_tok()
                if curTok is not None and curTok['name'] == ',':
                    curTok = get_next_tok()

            result.append({
                'label': labelTok['value'] if labelTok else None,
                'instr': idTok['value'],
                'args': args,
                'pos': idTok['pos']
            })

    def _parseError(self, pos, msg):
        raise ParseError(msg, pos)