"""The framework-spec parser — grammar-hosted binding.

dsl/framework-spec.dsl is the model; parse() yields the dict
consumers read: {"dsl": {name, version, framework, binding},
"vocabulary": {form: entry}, "locators": {rung: entry}}.

Grammar:
    spec     := 'framework' IDENT 'version' NUMBER? decl*
    decl     := 'vocabulary' '{' form* '}' | 'locators' '{' rung* '}'
    form     := 'form' IDENT '{' member* '}'
    rung     := 'rung' IDENT '{' member* '}'
    member   := 'arg' IDENT STRING? | 'caption' STRING | 'key' IDENT
              | ('python'|'java') STRING          # single spell
              | 'variants' '{' variant* '}'
              | 'lines' '{' (lang STRING)* '}'    # spell as line list
              | 'wrap' '{' (lang 'pre'|'post' STRING)* '}'
    variant  := 'on' IDENT (',' IDENT)* '{' (lang STRING)* '}'
    STRING   := '"' esc '"' | TRIPLE raw TRIPLE   # TRIPLE = three '"'
    comment  := '#' to end of line
"""


def parse(text):
    """DSL text → the model dict."""
    return _Parser(_lex(text)).spec()


def _lex(text):
    toks = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
        elif c.isspace():
            i += 1
        elif text.startswith('"""', i):
            j = text.index('"""', i + 3)
            toks.append(("str", text[i + 3:j]))
            i = j + 3
        elif c == '"':
            j, buf = i + 1, ""
            while text[j] != '"':
                if text[j] == "\\":
                    j += 1
                buf += text[j]
                j += 1
            toks.append(("str", buf))
            i = j + 1
        elif c in "{},":
            toks.append((c, c))
            i += 1
        else:
            j = i
            while j < n and (not text[j].isspace()
                             and text[j] not in '{}",#'):
                j += 1
            toks.append(("id", text[i:j]))
            i = j
    return toks


_RESERVED = {"arg", "caption", "key", "variants", "lines", "wrap",
             "python", "java", "on", "pre", "post", "form", "rung",
             "framework", "version", "vocabulary", "locators"}


class _Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def _peek(self):
        return self.toks[self.i][0] if self.i < len(self.toks) else None

    def _take(self, kind=None):
        if self.i >= len(self.toks):
            raise SyntaxError("unexpected end of dsl")
        t = self.toks[self.i]
        if kind and t[0] != kind:
            raise SyntaxError("expected %r, got %r (%s)"
                              % (kind, t[0], t[1][:40]))
        self.i += 1
        return t[1]

    def spec(self):
        self._take("id")  # 'framework'
        fw = self._take("id")
        self._take("id")  # 'version'
        ver = self._take("id")
        m = {"dsl": {"name": "framework-spec", "framework": fw,
                     "version": int(ver), "binding": "grammar-hosted"},
             "vocabulary": {}, "locators": {}}
        while self._peek() is not None:
            kw = self._take("id")
            if kw in ("vocabulary", "locators"):
                kind = "form" if kw == "vocabulary" else "rung"
                self._take("{")
                while self._peek() != "}":
                    self._take("id")  # 'form'|'rung'
                    name = self._take("id")
                    m[kw][name] = self._body()
                self._take("}")
            else:
                raise SyntaxError("expected vocabulary|locators, got %r" % kw)
        return m

    def _body(self):
        self._take("{")
        e = {"arg": {}}
        while self._peek() != "}":
            kw = self._take("id")
            if kw == "arg":
                nm = self._take("id")
                nxt = self.toks[self.i] if self.i < len(self.toks) else (None, None)
                if nxt[0] == "str" or (
                        nxt[0] == "id" and nxt[1] not in _RESERVED):
                    e["arg"][nm] = self._take(nxt[0])
                else:
                    e["arg"][nm] = nm
            elif kw == "caption":
                e["caption"] = self._take("str")
            elif kw == "key":
                e["key"] = self._take("id")
            elif kw == "variants":
                e["variants"] = self._variants()
            elif kw == "lines":
                e["spell"] = self._langs_list()
            elif kw == "wrap":
                e["wrap"] = self._wrap()
            elif kw in ("python", "java"):
                e.setdefault("spell", {})[kw] = self._take("str")
                # rhs evaluated before subscript — no subscript take here
            else:
                raise SyntaxError("unknown member %r" % kw)
        self._take("}")
        if len(e["arg"]) == 1:
            e["arg"] = next(iter(e["arg"].values()))
        return e

    def _variants(self):
        self._take("{")
        out = []
        while self._peek() != "}":
            self._take("id")  # 'on'
            keys = []
            while self._peek() != "{":
                if self._peek() == ",":
                    self._take(",")
                else:
                    keys.append(self._take("id"))
            self._take("{")
            sp = {}
            while self._peek() != "}":
                lang = self._take("id")
                sp[lang] = self._take("str")
            self._take("}")
            out.append({"when": keys, "spell": sp})
        self._take("}")
        return out

    def _langs_list(self):
        """lines {} — per-language ordered spell lists."""
        self._take("{")
        sp = {}
        while self._peek() != "}":
            sp.setdefault(self._take("id"), []).append(self._take("str"))
        self._take("}")
        return sp

    def _wrap(self):
        """wrap {} — per-language pre/post line lists."""
        self._take("{")
        w = {}
        while self._peek() != "}":
            lang, side = self._take("id"), self._take("id")
            w.setdefault(lang, {}).setdefault(side, []).append(
                self._take("str"))
        self._take("}")
        return w
